# The Ancient Land Adventure Report

## Project overview

The Ancient Land Adventure is a text-based command-line game written in Python. The player takes the role of an explorer searching for a legendary treasure. The game collects the player's name, presents two possible locations, and then asks for a second decision within the selected location.

The game is designed to demonstrate:

- Functions and return values
- Conditional branching
- Repeated input validation with `while` loops
- String formatting with f-strings
- A replay loop for multiple rounds
- A simple win-or-lose game state

## Objective

The objective is to reach the treasure chamber by selecting the correct action at each stage of the adventure.

A round is won when the player:

1. Follows the river through the forest, or
2. Lights the torch inside the cave.

A round is lost when the player:

1. Climbs the tall tree, or
2. Proceeds through the cave in the dark.

## Gameplay flow

1. The game prints its title and introduction.
2. The player enters a name. A blank name is replaced with `Explorer`.
3. The player chooses the dark forest or the mysterious cave.
4. The selected path presents a second decision.
5. The path function returns `True` for success or `False` for failure.
6. `main()` displays the result and asks whether to restart.
7. The game continues until the player enters something other than `y` or `yes` when asked to replay.

## Decision outcomes

| Location | Choice | Result | Round status |
|---|---|---|---|
| Dark forest | Follow the river | Find a bridge leading to the treasure chamber | Win |
| Dark forest | Climb a tall tree | A broken branch causes the explorer to fall | Lose |
| Mysterious cave | Light the torch | Ancient markings lead to the legendary treasure | Win |
| Mysterious cave | Proceed in the dark | The explorer loses the way | Lose |

## Program structure

| Function | Responsibility | Return value |
|---|---|---|
| `forest_path(player_name)` | Displays the forest scene and processes the river or tree choice | `True` for river, `False` for tree |
| `cave_path(player_name)` | Displays the cave scene and processes the torch or darkness choice | `True` for torch, `False` for darkness |
| `start_game()` | Starts one round, collects the player's name, and selects a path | The selected path's Boolean result |
| `main()` | Runs rounds, prints the result, and controls replay | No explicit return value |

## Input handling

The game accepts choices as text and removes surrounding whitespace with `.strip()`. Path selections accept only `1` or `2`. Invalid selections do not end the game; the player is shown `Please choose 1 or 2.` and prompted again.

Replay input is converted to lowercase with `.lower()`. The values `y` and `yes` start another round. Any other value exits the game.

## Technical details

- Language: Python
- Interface: Command line
- External dependencies: None
- Entry point: The `main()` function is called when the file is run directly.
- Source file: `adventure_game.py`

## How to run

From the `Adventure Game` folder, run:

```text
python adventure_game.py
```

## Example test scenarios

| Scenario | Inputs | Expected result |
|---|---|---|
| Forest win | `Alex`, `1`, `1`, `n` | Alex finds the treasure and the game exits |
| Forest loss | `Alex`, `1`, `2`, `n` | Alex does not complete the quest and the game exits |
| Cave win | `Alex`, `2`, `1`, `n` | Alex finds the treasure and the game exits |
| Cave loss | `Alex`, `2`, `2`, `n` | Alex does not complete the quest and the game exits |
| Default name | Blank name, then a valid path | The game uses `Explorer` as the player name |
| Invalid choice | Any invalid path input followed by `1` or `2` | The game displays an error and asks again |
| Replay | A winning or losing round followed by `y` | A new round begins |

## Strengths and possible extensions

The game has a small, readable structure and clear separation between the main flow and each adventure path. Boolean return values make it easy for `main()` to display the correct result after a round.

Possible future improvements include:

- Add more locations and branching decisions
- Track a score, inventory, or number of attempts
- Add multiple treasure endings
- Validate replay input with a dedicated helper function
- Add automated tests by injecting input rather than reading directly from the console
- Add colored terminal output or simple sound effects

## Conclusion

The Ancient Land Adventure is a compact example of an interactive Python program. Its branching choices, validation loops, and replay behavior create a complete playable experience while keeping the implementation easy to understand and extend.
