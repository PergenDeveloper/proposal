import os
import secrets

from itertools import chain
from typing import Iterable, Tuple, Union

from django.core.files.storage import default_storage
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
)
from django.db.models.fields.files import FileField

import graphene
from graphene.types.mutation import MutationOptions

from ...core.exceptions import PermissionDenied
from .types.errors import UploadError
from .types import File, Upload
from .handle_errors import get_error_fields, validation_error_to_error_type


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    object_type = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        description=None,
        permissions: Tuple = None,
        _meta=None,
        error_type_class=None,
        **options,
    ):
        if not _meta:
            _meta = MutationOptions(cls)

        if not description:
            raise ImproperlyConfigured("No description provided in Meta")

        if not error_type_class:
            raise ImproperlyConfigured("No error_type_class provided in Meta.")

        if isinstance(permissions, str):
            permissions = (permissions,)

        if permissions and not isinstance(permissions, tuple):
            raise ImproperlyConfigured(
                "Permissions should be a tuple or a string in Meta"
            )

        _meta.permissions = permissions
        _meta.error_type_class = error_type_class
        super().__init_subclass_with_meta__(
            description=description, _meta=_meta, **options
        )
        cls._meta.fields.update(get_error_fields(error_type_class))

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def get_instance_or_error(cls, info, id, model, field):
        instance = model.objects.filter(pk=id).first()
        if not instance:
            raise ValidationError(
                {
                    field: ValidationError(
                        f"Instance with this id doesn't exists.", code="not_found"
                    )
                }
            )
        return instance

    @classmethod
    def get_instances_or_error(cls, info, ids, model, field):
        instances = list(model.objects.filter(pk__in=ids))
        if not instances:
            raise ValidationError(
                {
                    field: ValidationError(
                        f"Instances not found.", code="not_found"
                    )
                }
            )
        return instances

    @classmethod
    def clean_instance(cls, info, instance):
        """Clean the instance that was created using the input data.
        Once an instance is created, this method runs `full_clean()` to perform
        model validation.
        """
        try:
            instance.full_clean()
        except ValidationError as error:
            if hasattr(cls._meta, "exclude"):
                # Ignore validation errors for fields that are specified as
                # excluded.
                new_error_dict = {}
                for field, errors in error.error_dict.items():
                    if field not in cls._meta.exclude:
                        new_error_dict[field] = errors
                error.error_dict = new_error_dict

            if error.error_dict:
                raise error

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        """Fill instance fields with cleaned data.
        The `instance` argument is either an empty instance of a already
        existing one which was fetched from the database. `cleaned_data` is
        data to be set in instance fields. Returns `instance` with filled
        fields, but not saved to the database.
        """
        from django.db import models

        opts = instance._meta

        for f in opts.fields:
            if any(
                [
                    not f.editable,
                    isinstance(f, models.AutoField),
                    f.name not in cleaned_data,
                ]
            ):
                continue
            data = cleaned_data[f.name]
            if data is None:
                # We want to reset the file field value when None was passed
                # in the input, but `FileField.save_form_data` ignores None
                # values. In that case we manually pass False which clears
                # the file.
                if isinstance(f, FileField):
                    data = False
                if not f.null:
                    data = f._get_default()
            f.save_form_data(instance, data)
        return instance

    @classmethod
    def check_permissions(cls, context, permissions=None):
        """Determine whether user or app has rights to perform this mutation.
        Default implementation assumes that account is allowed to perform any
        mutation. By overriding this method or defining required permissions
        in the meta-class, you can restrict access to it.
        The `context` parameter is the Context instance associated with the request.
        """
        permissions = permissions or cls._meta.permissions
        if not permissions:
            return True
        if context.user.has_perms(permissions):
            return True
        return False

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        try:
            response = cls.perform_mutation(root, info, **data)
            if response.errors is None:
                response.errors = []
            return response
        except ValidationError as e:
            return cls.handle_errors(e)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        pass

    @classmethod
    def handle_errors(cls, error: ValidationError, **extra):
        """Return class instance with errors."""
        error_list = validation_error_to_error_type(error, cls._meta.error_type_class)
        return cls(errors=error_list, **extra)


class ModelMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        arguments=None,
        model=None,
        exclude=None,
        return_field_name=None,
        object_type=None,
        _meta=None,
        **options,
    ):
        if not model:
            raise ImproperlyConfigured("model is required for ModelMutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)

        if exclude is None:
            exclude = []

        if not return_field_name:
            return_field_name = get_model_name(model)
        if arguments is None:
            arguments = {}

        _meta.model = model
        _meta.object_type = object_type
        _meta.return_field_name = return_field_name
        _meta.exclude = exclude
        super().__init_subclass_with_meta__(_meta=_meta, **options)

        model_type = cls.get_type_for_model()
        if not model_type:
            raise ImproperlyConfigured(
                f"GraphQL type for model {cls._meta.model.__name__} could not be "
                f"resolved for {cls.__name__}"
            )
        fields = {return_field_name: graphene.Field(model_type)}

        cls._update_mutation_arguments_and_fields(arguments=arguments, fields=fields)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        """Clean input data received from mutation arguments.
        Fields containing UUIDs or lists of UUIDs are automatically resolved into
        model instances. `instance` argument is the model instance the mutation
        is operating on (before setting the input data). `input` is raw input
        data the mutation receives.
        Override this method to provide custom transformations of incoming
        data.
        """

        def is_list_of_ids(field):
            if isinstance(field.type, graphene.List):
                of_type = field.type.of_type
                if isinstance(of_type, graphene.NonNull):
                    of_type = of_type.of_type
                return of_type == graphene.UUID
            return False

        def is_id_field(field):
            return (
                field.type == graphene.UUID
                or isinstance(field.type, graphene.NonNull)
                and field.type.of_type == graphene.UUID
            )

        def is_upload_field(field):
            if hasattr(field.type, "of_type"):
                return field.type.of_type == Upload
            return field.type == Upload

        if not input_cls:
            input_cls = getattr(cls.Arguments, "input")
        cleaned_input = {}

        for field_name, field_item in input_cls._meta.fields.items():
            if field_name not in data:
                continue
            
            value = data[field_name]
                
            # handle list of IDs field
            if value is not None and is_list_of_ids(field_item):
                opts = instance._meta
                # check if field has relation and then get instances.
                field_model_class = opts.get_field(field_name).related_model
                if field_model_class:
                    cleaned_input[field_name] = cls.get_instances_or_error(
                        info, value, model=field_model_class, field=field_name
                    )

            # handle ID field
            elif value is not None and is_id_field(field_item):
                opts = instance._meta
                # check if field has relation and then get instance.
                field_model_class = opts.get_field(field_name).related_model
                if field_model_class:
                    cleaned_input[field_name] = cls.get_instance_or_error(
                        info, value, model=field_model_class, field=field_name
                    )
                    

            # handle uploaded files
            elif value is not None and is_upload_field(field_item):
                value = info.context.FILES.get(value)
                cleaned_input[field_name] = value

            # handle other fields
            else:
                cleaned_input[field_name] = value
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        opts = instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, "save_form_data"):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, "errors": []})

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

    @classmethod
    def get_type_for_model(cls):
        if not cls._meta.object_type:
            raise ImproperlyConfigured(
                f"Either GraphQL type for model {cls._meta.model.__name__} needs to be "
                f"specified on object_type option or {cls.__name__} needs to define "
                "custom get_type_for_model() method."
            )

        return cls._meta.object_type

    @classmethod
    def get_instance(cls, info, **data):
        """Retrieve an instance from the supplied global id.
        The expected graphene type can be lazy (str).
        """
        object_id = data.get("id")
        if object_id:
            instance = cls.get_instance_or_error(
                info, object_id, cls._meta.model, field="id"
            )
        else:
            instance = cls._meta.model()
        return instance

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        """Perform an action after saving an object and its m2m."""
        pass

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform model mutation.
        Depending on the input data, `mutate` either creates a new instance or
        updates an existing one. If `id` argument is present, it is assumed
        that this is an "update" mutation. Otherwise, a new instance is
        created based on the model associated with this mutation.
        """
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)


class ModelDeleteMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic before deleting the model instance.
        Override this method to raise custom validation error and abort
        the deletion process.
        """

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        instance_id = data.get("id")
        instance = cls.get_instance_or_error(
            info, instance_id, cls._meta.model, field="id"
        )

        if instance:
            cls.clean_instance(info, instance)

        db_id = instance.id
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)


class BaseBulkMutation(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many objects were affected."
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, model=None, object_type=None, _meta=None, **kwargs
    ):
        if not model:
            raise ImproperlyConfigured("model is required for bulk mutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)
        _meta.model = model
        _meta.object_type = object_type

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def get_type_for_model(cls):
        if not cls._meta.object_type:
            raise ImproperlyConfigured(
                f"Either GraphQL type for model {cls._meta.model.__name__} needs to be "
                f"specified on object_type option or {cls.__name__} needs to define "
                "custom get_type_for_model() method."
            )

        return cls._meta.object_type

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic.
        Override this method to raise custom validation error and prevent
        bulk action on the instance.
        """

    @classmethod
    def bulk_action(cls, info, queryset, **kwargs):
        """Implement action performed on queryset."""
        raise NotImplementedError

    @classmethod
    def perform_mutation(cls, _root, info, ids, **data):
        """Perform a mutation that deletes a list of model instances."""
        clean_instance_ids, errors = [], {}
        # Allow to pass empty list for dummy mutation
        if not ids:
            return 0, errors
        instance_model = cls._meta.model
        model_type = cls.get_type_for_model()
        if not model_type:
            raise ImproperlyConfigured(
                f"GraphQL type for model {cls._meta.model.__name__} could not be "
                f"resolved for {cls.__name__}"
            )

        try:
            instances = cls.get_instances_or_error(
                info, ids, instance_model, field="id",
            )
        except ValidationError as error:
            return 0, error
        for instance, instance_id in zip(instances, ids):
            instance_errors = []

            # catch individual validation errors to raise them later as
            # a single error
            try:
                cls.clean_instance(info, instance)
            except ValidationError as e:
                msg = ". ".join(e.messages)
                instance_errors.append(msg)

            if not instance_errors:
                clean_instance_ids.append(instance.pk)
            else:
                instance_errors_msg = ". ".join(instance_errors)
                ValidationError({instance_id: instance_errors_msg}).update_error_dict(
                    errors
                )

        if errors:
            errors = ValidationError(errors)
        count = len(clean_instance_ids)
        if count:
            qs = instance_model.objects.filter(pk__in=clean_instance_ids)
            cls.bulk_action(info=info, queryset=qs, **data)
        return count, errors

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        count, errors = cls.perform_mutation(root, info, **data)
        if errors:
            return cls.handle_errors(errors, count=count)

        return cls(errors=errors, count=count)


class ModelBulkDeleteMutation(BaseBulkMutation):
    class Meta:
        abstract = True

    @classmethod
    def bulk_action(cls, info, queryset):
        queryset.delete()


class FileUpload(BaseMutation):
    uploaded_file = graphene.Field(File)

    class Arguments:
        file = Upload(
            required=True, description="Represents a file in a multipart request."
        )

    class Meta:
        description = (
            "Upload a file. This mutation must be sent as a `multipart` "
            "request. More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        error_type_class = UploadError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        file_data = info.context.FILES.get(data["file"])

        # add unique text fragment to the file name to prevent file overriding
        file_name, format = os.path.splitext(file_data._name)
        hash = secrets.token_hex(nbytes=4)
        new_name = f"file_upload/{file_name}_{hash}{format}"

        path = default_storage.save(new_name, file_data.file)

        return FileUpload(
            uploaded_file=File(url=path, content_type=file_data.content_type)
        )