# A text-based adventure game about finding a legendary treasure.


def forest_path(player_name):
    """Guide the explorer through the dark forest."""
    print("\nThe forest is dense and quiet. You hear rushing water nearby.")
    print("1. Follow the river")
    print("2. Climb a tall tree")

    while True:
        choice = input("Choose 1 or 2: ").strip()
        if choice == "1":
            print(
                f"\n{player_name} follows the river and discovers a bridge leading "
                "to the treasure chamber!"
            )
            return True
        if choice == "2":
            print(
                "\nThe tree branch breaks, and the fall leaves you unable to continue."
            )
            return False
        print("Please choose 1 or 2.")


def cave_path(player_name):
    """Guide the explorer through the mysterious cave."""
    print("\nThe cave entrance is cold and shadowy. You find an old torch.")
    print("1. Light the torch")
    print("2. Proceed in the dark")

    while True:
        choice = input("Choose 1 or 2: ").strip()
        if choice == "1":
            print(
                f"\n{player_name} lights the torch and follows ancient markings "
                "to the legendary treasure!"
            )
            return True
        if choice == "2":
            print("\nYou lose your way in the darkness. The quest is over.")
            return False
        print("Please choose 1 or 2.")


def start_game():
    """Start one round of the adventure and return whether it was won."""
    print("\n=== The Ancient Land Adventure ===")
    print("You are an explorer searching for a legendary treasure.")
    player_name = input("What is your name, explorer? ").strip() or "Explorer"

    print(f"\nWelcome, {player_name}! Choose your path:")
    print("1. Explore the dark forest")
    print("2. Enter the mysterious cave")

    while True:
        choice = input("Choose 1 or 2: ").strip()
        if choice == "1":
            return forest_path(player_name)
        if choice == "2":
            return cave_path(player_name)
        print("Please choose 1 or 2.")


def main():
    """Run the game until the player chooses to stop."""
    print("Adventure game setup complete!")
    while True:
        won = start_game()
        if won:
            print("\nYou found the treasure and completed the quest!")
        else:
            print("\nYou did not complete the quest this time.")

        replay = input("Would you like to restart the game? (y/n): ").strip().lower()
        if replay not in {"y", "yes"}:
            print("\nThanks for playing!")
            break


if __name__ == "__main__":
    main()
