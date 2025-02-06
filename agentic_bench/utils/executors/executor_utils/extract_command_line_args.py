import re

def extract_command_line_args(lang, filename, human_input_or_command_line_args):
    human_input_or_command_line_args = " ".join(human_input_or_command_line_args).strip()
    
    extension = filename.split('.')[-1] if '.' in filename else 'py' if lang.startswith('python') else lang
    
    # Define prefixes to remove
    prefixes = [f"{lang} {filename}", f"{lang}", f"{filename}"]
    for prefix in prefixes:
        if human_input_or_command_line_args.startswith(prefix):
            human_input_or_command_line_args = human_input_or_command_line_args[len(prefix):].strip()
            break
    
    # Split into arguments and filter out matches of *.extension
    args = human_input_or_command_line_args.split()
    args = [arg for arg in args if not re.fullmatch(rf".*\.{extension}", arg)]
    
    return args