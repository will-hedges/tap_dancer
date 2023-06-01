import os
from pathlib import Path


def kc_is_num(keycode):
    try:
        isinstance(int(keycode[0]), int)
        return True
    except ValueError:
        return False


def read_in_tap_holds():
    os.chdir(Path(__file__).parent)
    with open("tap_holds.txt", "r") as infile:
        key_pairs = sorted(
            [
                line.strip()
                for line in infile.readlines()
                if not line.startswith("*") and line != "\n"
            ]
        )
        tap_holds = []
        for key_pair in key_pairs:
            tap, hold = key_pair.split(",")

            alias = tap
            tap_is_num = kc_is_num(tap)
            if tap_is_num:
                alias = "N" + tap

            tap_holds.append((tap.strip(), hold.strip(), alias.strip()))

    return tap_holds


def create_file_string(tap_holds):
    tap_dance_enums = []
    tap_dance_functions = []
    tap_dance_instances = []
    tap_dance_actions = []
    tap_dance_definitions = []

    for index, (tap, hold, alias) in enumerate(tap_holds):
        TAP, tap = tap.upper(), tap.lower()
        HOLD, hold = hold.upper(), hold.lower()
        ALIAS, alias = alias.upper(), alias.lower()

        # add the enum/name string to the enum list
        name = f"{ALIAS}_{HOLD}"
        tap_dance_enums.append(f"\t{name} = {index}")

        # add the 'finished' and 'reset' functions to the function list
        finished = f"{alias}_finished"
        reset = f"{alias}_reset"
        statement = " (qk_tap_dance_state_t *state, void *user_data);"
        tap_dance_functions += [finished + statement, reset + statement + "\n"]

        # create a big string for the instance
        tap_dance_instances.append(
            "\n".join(
                (
                    f"// instance 'tap' for the {name} tap dance",
                    f"static tap {alias}tap_state = {{",
                    "\t.is_press_action = true,",
                    "\t.state = 0",
                    "};",
                    f"void {alias}_finished (qk_tap_dance_state_t *state, void *user_data) {{",
                    f"\t{alias}tap_state.state = cur_dance(state);",
                    f"\tswitch ({alias}tap_state.state) {{",
                    "\t\tcase SINGLE_TAP:",
                    f"\t\t\tregister_code(KC_{TAP});",
                    "\t\t\tbreak;",
                    "\t\tcase SINGLE_HOLD:",
                    f"\t\t\tregister_code(KC_{HOLD});",
                    "\t\t\tbreak;",
                    f"void {alias}_reset (qk_tap_dance_state_t *state, void *user_data) {{",
                    f"\tswitch ({alias}tap_state.state) {{",
                    "\t\tcase SINGLE_TAP:",
                    f"\t\t\tunregister_code(KC_{TAP});",
                    "\t\t\tbreak;",
                    "\t\tcase SINGLE_HOLD:",
                    f"\t\t\tunregister_code(KC_{HOLD});",
                    "\t\t\tbreak;",
                    "\t}",
                    f"\t{alias}tap_state.state = 0;",
                    "};",
                )
            )
        )

        # create a string for the action + add it to the action list
        tap_dance_actions.append(
            f"\t[{name}] = ACTION_TAP_DANCE_FN_ADVANCED(NULL, {finished}, {reset})"
        )

        # create a string for the definition and add it to the definition list
        tap_dance_definitions.append(f"#define {name} TD({name})")

    # create the document
    file_contents = "\n".join(
        (
            "// Setting up Tap Dance for tap vs. hold",
            "typedef struct {",
            "\tbool is_press_action;",
            "\tint state;",
            "} tap;",
            "",
            "// Tap Dance states",
            "enum {",
            "\tSINGLE_TAP = 1,",
            "\tSINGLE_HOLD = 2",
            "};",
            "",
            "// Tap dance enums",
            "enum {",
            ",\n".join(tap_dance_enums),
            "};",
            "\n",
            "int cur_dance (qk_tap_dance_state_t *state);",
            "",
            "// For tap dance, put void statements here so they can be used in any keymap.",
            "\n".join(tap_dance_functions),
            "",
            "// Determine tap state",
            "int cur_dance (qk_tap_dance_state_t *state) {",
            "\tif (state->interrupted || !state->pressed) {",
            "\t\treturn SINGLE_TAP;",
            "\t} else {",
            "\t\treturn SINGLE_HOLD;",
            "\t}",
            "};",
            "\n",
            "\n\n".join(tap_dance_instances),
            "\n",
            "// Tap Dance actions",
            "qk_tap_dance_action_t tap_dance_actions[] = {",
            ",\n".join(tap_dance_actions),
            "};",
            "\n",
            "// These are the Tap Dance keycodes to add to your keymap.c",
            "\n".join(tap_dance_definitions),
            "",
        )
    )
    return file_contents


def write_out_c_file(file_contents):
    with open("tap_dances.c", "w") as outfile:
        outfile.write(file_contents)


def main():
    kc_pairs = read_in_tap_holds()
    tap_dances = create_file_string(kc_pairs)
    write_out_c_file(tap_dances)
    return


main()
