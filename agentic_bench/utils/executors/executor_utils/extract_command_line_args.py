def extract_command_line_args(lang, filename, human_input_or_command_line_args):
    # Remove leading/trailing whitespace
    human_input_or_command_line_args = " ".join(human_input_or_command_line_args)
    human_input_or_command_line_args = human_input_or_command_line_args.strip()
    
    # Check if the human_input_or_command_line_args starts with the language and filename
    prefix1 = f"{lang} {filename}"
    prefix2 = f"{lang}"
    prefix3 = f"{filename}"
    
    if human_input_or_command_line_args.startswith(prefix1):
        # Extract the part after the language and filename
        args_part = human_input_or_command_line_args[len(prefix1):].strip()
        # Split the arguments into a list
        args = args_part.split()
        return args
    elif human_input_or_command_line_args.startswith(prefix2):
        # Extract the part after the language and filename
        args_part = human_input_or_command_line_args[len(prefix2):].strip()
        # Split the arguments into a list
        args = args_part.split()
        return args
    elif human_input_or_command_line_args.startswith(prefix3):
        # Extract the part after the language and filename
        args_part = human_input_or_command_line_args[len(prefix3):].strip()
        # Split the arguments into a list
        args = args_part.split()
        return args
    else:
        # If the human_input_or_command_line_args does not start with the language and filename,
        # assume the entire input is the command line arguments
        args = human_input_or_command_line_args.split()
        return args