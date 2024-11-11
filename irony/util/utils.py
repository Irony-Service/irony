def replace_keys_with_values(input_string, replacements):
    for key, value in replacements.items():
        input_string = input_string.replace(key, value)
    return input_string
