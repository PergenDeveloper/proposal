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

That way the fontend know exactly what is happening.

The main classes to understand are `BaseMutation` and `ModelMutation`.

## Install and active virtual env
> `python3 -m venv proposal`
>
> `source  proposal/bin/activate`

## Download the project
> `git clone https://github.com/PergenDeveloper/proposal.git`
>
> `cd proposal`
> 
> `pip install requirements.txt`


I hope you like it 😊.
