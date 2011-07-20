import colander

REGISTER_NAME_RE = r"^[a-zA-Z0-9_\-]{3,255}$"

class Register(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(),
                               validator=colander.Regex(REGISTER_NAME_RE))

    fullname = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String(),
                                validator=colander.Email())
    password1 = colander.SchemaNode(colander.String(),
                                    validator=colander.Length(min=4))
    password2 = colander.SchemaNode(colander.String(),
                                    validator=colander.Length(min=4))


class Settings(colander.MappingSchema):
    fullname = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String(),
                                validator=colander.Email())
    password1 = colander.SchemaNode(colander.String())
    password2 = colander.SchemaNode(colander.String())
