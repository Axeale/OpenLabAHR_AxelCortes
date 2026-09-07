import re


ACTION_WORDS = {
	"pick": "pick",
	"pickup": "pick",
	"pick up": "pick",
	"take": "pick",
	"grab": "pick",
	"drop": "drop",
	"put": "place",
	"place": "place",
	"set": "place",
}


def parse_intent(command):
	"""Extract the object, action, and destination from a short command."""
	text = command.strip().lower()

	action = None
	action_start = len(text)
	for phrase, normalized_action in sorted(ACTION_WORDS.items(), key=lambda item: -len(item[0])):
		match = re.search(rf"\b{re.escape(phrase)}\b", text)
		if match and match.start() < action_start:
			action = normalized_action
			action_start = match.start()

	if action is None:
		return {"object": None, "action": None, "where": None}

	before_action = text[:action_start].strip(" ,.")
	after_action = text[action_start + len(next(
		phrase for phrase, normalized in sorted(ACTION_WORDS.items(), key=lambda item: -len(item[0]))
		if normalized == action and re.search(rf"\b{re.escape(phrase)}\b", text[action_start:])
	)):].strip(" ,.")

	# In commands such as "pick up the red cube", the object follows the action.
	if action == "pick":
		object_text = re.sub(r"^(up\s+)?(?:the\s+)?", "", after_action).strip()
		destination = None
	else:
		parts = re.split(r"\s+(?:in|into|on|onto|at|to)\s+", after_action, maxsplit=1)
		object_text = re.sub(r"^(?:the\s+)?", "", parts[0]).strip()
		destination = parts[1].strip() if len(parts) == 2 else None

	# Support commands phrased as "the cube, then place it on the table".
	if action == "pick" and before_action:
		object_text = re.sub(r"^(?:please\s+)?(?:the\s+)?", "", before_action).strip()

	return {
		"object": object_text or None,
		"action": action,
		"where": destination,
	}


def main():
	print("Describe an action (for example: 'pick up the red cube' or 'place the cube on the table').")
	command = input("> ")
	intent = parse_intent(command)

	print("\nIntent:")
	print(f"Object: {intent['object'] or 'not found'}")
	print(f"Action: {intent['action'] or 'not found'}")
	print(f"Where: {intent['where'] or 'not specified'}")


if __name__ == "__main__":
	main()
