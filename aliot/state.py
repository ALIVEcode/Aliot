import json
from dataclasses import fields, Field


class AliotObjState:
    def as_doc(self, document_name="document"):
        if not hasattr(self, "__dataclass_fields__"):
            # if the child object is not a dataclass, we return the object as a dict formatted with the document name
            return {f"/{document_name}/{key}": val for key, val in self.__dict__.items()}

        def field_is_included(field: Field):
            # returns True if the metadata does not contain "as_doc" or if it contains "as_doc" and it is True
            return field.metadata.get("as_doc", True)

        # noinspection PyDataclass
        return {f"/{document_name}/{field.name}": getattr(self, field.name) for field in fields(self) if
                field_is_included(field)}

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)
