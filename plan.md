# Secrets management plan

1. Let the users pass in a secrets class
2. Each field gets passed into the env by us. This `env` is where the browser is running.

Note that the user's class might be something like:

```python3
class Secrets:
	...
	def resolve(self) -> dict:
		# This is a crucial function
		...

from pyba import Engine

Engine(..., secrets=Secrets)
```

On our side, 

1. we need to have a generic type for the password manager
2. try to hit the resolve endpoint and pass that to the browser session env
3. if no resolve endpoint, then throw an error

```python3
from typing import Protocol, runtime_checkable

@runtime_checkable
class PasswordManager(Protocol):
	def resolve(self) -> dict[str, str]:
		...

def extract_secrets(secret_manager: PasswordManager | None) -> dict[str, str]:
	if secret_manager is None:
		return {}

	if not hasattr(secret_manager, "resolve"):
		raise NotImplementedError(
			"Password manager must implement a resolve() -> dict[str, str] method"
		)

	secrets = secret_manager.resolve()

	if not isinstance(secrets, dict):
		raise TypeError("resolve() must return dict[str, str]")

	return secrets

# All that happens beforehand and now inside base engines
import os

def __init__(self, ...):
	self.secrets: dict[str, str] = extract_secrets(Secrets)

	# So even if its None, its fine
	for k, v in self.secrets.items():
	    os.environ[k] = v
```

And that's the idea.