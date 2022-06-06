
import json


class ObjectState:
	def to_dict(self, document_name="document"):
		d = {}
		for key, val in self.__dict__.items():
			d[f"/{document_name}/{key}"] = val
		return d

	def __str__(self):
		return json.dumps(self.to_dict(), indent=2)