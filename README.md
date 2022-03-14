# PROPOSAL

This project is a proposal of how manage validation in mutations and return custom errors
to the front-end with the following schema without using graphene-django:

`
{
    field: "some-field",
    message: "error message",
    code: "custom-code-generated"
}
`

That way the fontend now exactly what is happening.

The main classes to understand are `BaseMutation` and `ModelMutation`.

## Instalar y activar un entorno virtual
> `python3 -m venv proposal`
>
> `source  idea-api/bin/activate`

## Clonar el proyecto
> `git clone https://github.com/PergenDeveloper/proposal.git`
>
> `cd proposal`
> `pip install requirements.txt`
