# yaml_processing.py


from validobj import parse_input, ValidationError


def parse_yaml_inp(inp, spec):
    try:
        return parse_input(inp, spec)
    except ValidationError as e:
        current_exc = e
        current_inp = inp
        error_text_lines = []
        while current_exc:
            if hasattr(current_exc, 'wrong_field'):
                wrong_field = current_exc.wrong_field
                # Mappings compping from ``round_trip_load`` have an
                # ``lc`` attribute that gives a tuple of
                # ``(line_number, column)`` for a given item in
                # the mapping.
                line = current_inp.lc.item(wrong_field)[0]
                error_text_lines.append(f"Problem processing key at line {line}:")
                current_inp = current_inp[wrong_field]
            elif hasattr(current_exc, 'wrong_index'):
                wrong_index = current_exc.wrong_index
                # Similarly lists allow to retrieve the line number for
                # a given item.
                line = current_inp.lc.item(wrong_index)[0]
                current_inp = current_inp[wrong_index]
                error_text_lines.append(f"Problem processing list item at line {line}:")
            elif hasattr(current_exc, 'unknown'):
                unknown_lines = []
                for u in current_exc.unknown:
                    unknown_lines.append((current_inp.lc.item(u)[0], u))
                unknown_lines.sort()
                for line, key in unknown_lines:
                    error_text_lines.append(
                        f"Unknown key {key!r} defined at line {line}:"
                    )
            error_text_lines.append(str(current_exc))
            current_exc = current_exc.__cause__
        raise ValidationError('\n'.join(error_text_lines)) from e
