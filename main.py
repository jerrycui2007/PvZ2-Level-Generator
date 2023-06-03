# PvZ2 Level Generator by Jerry Cui
# version 1.0.0
# Generates a basic level template. Levels are designed for PvZ2 Reflourished.

# Imports
from tkinter import *
from random import randint, choice
import json

FONT = "times new roman"


def main_menu():
    """
    Displays the main menu and options on the screen.
    """
    # Reset screen
    for widget in root.slaves():
        widget.destroy()

    title_label = Label(root, text="PvZ2 Level Generator")
    title_label.config(font=(FONT, 18))
    title_label.pack()

    # Contains all options where player can modify the level
    level_options_frame = Frame(root)

    difficulty_frame = Frame(level_options_frame)

    difficulty_label = Label(difficulty_frame, text="Level Difficulty: ")
    difficulty_label.config(font=(FONT, 12))
    difficulty_label.pack()

    # Set up difficulty selector
    difficulties = ["Easy", "Medium", "Hard"]
    selected_difficulty = StringVar()
    selected_difficulty.set("Medium")

    difficulty_option_menu = OptionMenu(difficulty_frame, selected_difficulty, *difficulties)
    difficulty_option_menu.config(font=(FONT, 12))
    difficulty_option_menu.pack()

    difficulty_frame.pack()

    generate_button = Button(level_options_frame, text="Generate Level",
                             command=lambda: generate_level(selected_difficulty.get()))
    generate_button.config(font=(FONT, 12))
    generate_button.pack()

    level_options_frame.pack()


def generate_level(difficulty):
    """
    Generates a level based off the difficulty given, and outputs it to a json file.
    1. Generate amount of waves and flags.
        - For easy, these are (10, 1), (10, 2), and (12, 2)
        - For medium, these are (12, 3), (15, 3), (16, 2), and (18, 3)
        - For hard, these are (16, 4), (18, 3), (20, 4), and (20, 5)
    2. Generate the zombies that come in each wave. Each wave has a point value and zombies are added until that point
    value is reached. Huge waves have double the zombie value in them
    :param difficulty: Either "Easy", "Medium", or "Hard", the possible difficulties
    3. Ambushes are generated on random waves, as well as flag waves. A random type of ambush is chosen, and then
    zombies are added into it, with point value equal to the regular wave
    """
    level = json.load(open("template.json"))  # base level template that the levels will be built on

    # Generate wave count and flags
    if difficulty == "Easy":
        wave_count, flags = choice([(10, 1), (10, 2), (12, 2)])
    elif difficulty == "Medium":
        wave_count, flags = choice([(12, 3), (15, 3), (16, 2), (18, 3)])
    else:  # difficulty is Hard
        wave_count, flags = choice([(16, 4), (18, 3), (20, 4), (20, 5)])

    flag_wave_interval = int(wave_count / flags)

    level["objects"][3]["objdata"]["FlagWaveInterval"] = flag_wave_interval  # 3 = WaveManagerProps
    level["objects"][3]["objdata"]["WaveCount"] = wave_count

    # Create zombie selection
    zombie_selection = set()
    zombie_types = json.load(open("zombies.json"))
    num_zombie_types = difficulty_to_int(difficulty) * 2 + 3  # number of non-fodder zombies that appear
    while len(zombie_selection) < num_zombie_types:
        zombie_type = choice(list(zombie_types["All Zombies"].items()))
        zombie_selection.add(zombie_type)  # adds a (zombie, zombie point) value pair
    # Add cannon fodder if it hasn't been added already
    zombie_selection.add(choice(list(zombie_types["Basics"].items())))
    zombie_selection.add(choice(list(zombie_types["Coneheads"].items())))
    zombie_selection.add(choice(list(zombie_types["Imps"].items())))

    # Generate wave content
    for wave_number in range(1, wave_count + 1):
        if wave_number % flag_wave_interval == 0:  # huge wave has 2x zombie spawns
            wave_data = enlist_zombies(get_wave_points(difficulty, wave_number) * 2, list(zombie_selection),
                                       wave_number)
        else:
            wave_data = enlist_zombies(get_wave_points(difficulty, wave_number), list(zombie_selection), wave_number)

        level["objects"].append(wave_data)

    # Generate wave pointers for the wave manager
    wave_pointers = []
    for wave_number in range(1, wave_count + 1):
        wave_pointers.append(["RTID(Wave" + str(wave_number) + "@CurrentLevel)"])
    level["objects"][3]["objdata"]["Waves"] = wave_pointers

    # Generate ambushes
    for wave_number in range(1, wave_count + 1):
        if randint(1, 8 - difficulty_to_int(difficulty)) == 1 or wave_number % flag_wave_interval == 0:
            # Random chance for ambush or on huge waves
            ambush_type = choice(["Sandstorm", "Raiding Party", "Bot Swarm", "Snowstorm"])
            if ambush_type == "Sandstorm":
                level["objects"].append(
                    enlist_zombies_sandstorm(get_wave_points(difficulty, wave_number), list(zombie_selection),
                                             wave_number, difficulty))
                # Add pointers to the ambushes
                level["objects"][3]["objdata"]["Waves"][wave_number - 1].append(
                    "RTID(Wave" + str(wave_number) + "StormEvent0@CurrentLevel)")
            elif ambush_type == "Raiding Party":
                level["objects"].append(
                    enlist_zombies_raiding_party(get_wave_points(difficulty, wave_number), wave_number))
                # Pointer
                level["objects"][3]["objdata"]["Waves"][wave_number - 1].append(
                    "RTID(Wave" + str(wave_number) + "RaidingPartyEvent0@CurrentLevel)")
            elif ambush_type == "Bot Swarm":
                level["objects"].append(
                    enlist_zombies_bot_swarm(get_wave_points(difficulty, wave_number), wave_number, difficulty))
                # Pointer
                level["objects"][3]["objdata"]["Waves"][wave_number - 1].append(
                    "RTID(Wave" + str(wave_number) + "SpiderRainEvent0@CurrentLevel)")
            elif ambush_type == "Snowstorm":
                level["objects"].append(
                    enlist_zombies_snowstorm(get_wave_points(difficulty, wave_number), list(zombie_selection),
                                             wave_number, difficulty))
                # Add pointers to the ambushes
                level["objects"][3]["objdata"]["Waves"][wave_number - 1].append(
                    "RTID(Wave" + str(wave_number) + "StormEvent0@CurrentLevel)")

    # The level is now finished! Just have to output it to a new .json file
    level["version"] = 1  # this little fucker wasted so much of my debugging time
    level_json = json.dumps(level, indent=4)
    with open("Future6.json", "w") as output_file:
        output_file.write(level_json)


def difficulty_to_int(difficulty):
    """
    Returns the integer representation of the difficulty selected. Easy is 1, Medium is 2, and Hard is 4
    :param difficulty: the String representing the difficulty
    :return: the integer representation
    """
    if difficulty == "Easy":
        return 1
    elif difficulty == "Medium":
        return 2
    else:  # difficulty is Hard:
        return 4


def get_wave_points(difficulty, wave_number):
    """
    Based on the difficulty, and what wave it is, return the "point" value of the zombies that can spawn this wave.
    This uses the equation, points = 2 * difficulty * ((wave_number - 1) // 3 + 1). So every three waves, the amount of
    zombies increments. Easy difficulty = 1, medium = 2, hard = 4.
    :param difficulty: The difficulty of the current level
    :param wave_number: What wave to generate
    """
    return 2 * ((wave_number - 1) // 3 + 1) * difficulty_to_int(difficulty)


def enlist_zombies(wave_points, zombie_types, wave_number):
    """
    Adds zombies into the current wave based on the possible zombie types and how much zombies to spawn in the wave, and
    also formats it in PvZ2 format. There is also one in five chance for wave to spawn plant food.
    :param wave_points: The "point" value of the current wave
    :param zombie_types: List of (zombie name, zombie point value) tuples
    :param wave_number: What wave to generate
    :return: wave, the wave dictionary formatted for PvZ2
    """
    # Wave template
    wave = {
        "aliases": [
            "Wave" + str(wave_number)
        ],
        "objclass": "SpawnZombiesJitteredWaveActionProps",
        "objdata": {
            "AdditionalPlantfood": 0,
            "Zombies": [
            ]
        }
    }

    current_points = 0  # points "spent" on zombies this wave
    zombies_in_wave = []  # contains the zombies in this wave (name only)

    while current_points < wave_points:
        possible_zombies = []  # list of zombies that can still be added based on points left
        for zombie in zombie_types:
            if zombie[1] <= (wave_points - current_points):  # check if the zombie's point value is low enough
                possible_zombies.append(zombie)
        try:
            added_zombie = choice(possible_zombies)
        except IndexError:  # when there are no possible options (should not happen anyway since imp is hardcoded)
            added_zombie = ("tutorial_imp", 1)
        zombies_in_wave.append(added_zombie[0])
        current_points += added_zombie[1]

    # Write the zombies to the wave data
    for zombie in zombies_in_wave:
        wave["objdata"]["Zombies"].append({"Type": "RTID(" + zombie + "@ZombieTypes)"})

    if randint(1, 15) in (1, 2):
        wave["objdata"]["AdditionalPlantfood"] = 1

    return wave


def enlist_zombies_sandstorm(wave_points, zombie_types, wave_number, difficulty):
    """
    Same function as enlist_zombies, but they are put into a Sandstorm instead.
    :param wave_points: The "point" value of the current wave
    :param zombie_types: List of (zombie name, zombie point value) tuples
    :param wave_number: What wave to generate
    :param difficulty: The wave difficulty
    :return: wave, the wave dictionary formatted for PvZ2
    """

    # Sandstorms should have their own list of zombies, but I'm too lazy to make that right now

    ambush = {
        "aliases": [
            "Wave" + str(wave_number) + "StormEvent0"
        ],
        "objclass": "StormZombieSpawnerProps",
        "objdata": {
            "ColumnEnd": 7,
            "ColumnStart": 6 - difficulty_to_int(difficulty),
            "GroupSize": randint(2, 4),
            "TimeBetweenGroups": 1,
            "Type": "sandstorm",
            "Waves": "",
            "WaveStartMessage": "[WARNING_SANDSTORM]",
            "Zombies": [

            ]
        }
    }

    # Copied code from the regular function. Can probably be optimized but I'll do that later

    current_points = 0  # points "spent" on zombies this wave
    zombies_in_wave = []  # contains the zombies in this wave (name only)

    while current_points < wave_points:
        possible_zombies = []  # list of zombies that can still be added based on points left
        for zombie in zombie_types:
            if zombie[1] <= (wave_points - current_points):  # check if the zombie's point value is low enough
                possible_zombies.append(zombie)
        try:
            added_zombie = choice(possible_zombies)
        except IndexError:  # when there are no possible options (should not happen anyway since imp is hardcoded)
            added_zombie = ("tutorial_imp", 1)
        zombies_in_wave.append(added_zombie[0])
        current_points += added_zombie[1]

    # Write the zombies to the wave data
    for zombie in zombies_in_wave:
        ambush["objdata"]["Zombies"].append({"Type": "RTID(" + zombie + "@ZombieTypes)"})

    return ambush


def enlist_zombies_raiding_party(wave_points, wave_number):
    """
    Creates a Raiding Party Ambush. The number of Swashbuckler Zombies is always wave_points // 2
    :param wave_points: The "point" value of the current wave
    :param wave_number: What wave to generate
    :return: wave, the wave dictionary formatted for PvZ2
    """

    ambush = {
        "aliases": [
            "Wave" + str(wave_number) + "RaidingPartyEvent0"
        ],
        "objclass": "RaidingPartyZombieSpawnerProps",
        "objdata": {
            "GroupSize": randint(1, 5),
            "SwashbucklerCount": wave_points // 2,
            "TimeBetweenGroups": "1",
            "WaveStartMessage": "Raiding Party!"
        }
    }

    return ambush


def enlist_zombies_bot_swarm(wave_points, wave_number, difficulty):
    """
    Creates a Bot Swarm Ambush. The number of Bots Zombies is always equal to wave points, and proximity is controlled
    by difficulty.
    :param wave_points: The "point" value of the current wave
    :param wave_number: What wave to generate
    :param difficulty: The level difficulty
    :return: wave, the wave dictionary formatted for PvZ2
    """

    ambush = {
                 "aliases": [
                     "Wave" + str(wave_number) + "SpiderRainEvent0"
                 ],
                 "objclass": "SpiderRainZombieSpawnerProps",
                 "objdata": {
                     "ColumnEnd": 8,
                     "ColumnStart": 6 - difficulty_to_int(difficulty),
                     "GroupSize": randint(1, wave_points // 5),
                     "SpiderCount": wave_points,
                     "SpiderZombieName": "future_imp",
                     "TimeBeforeFullSpawn": "1",
                     "TimeBetweenGroups": 0.2,
                     "WaveStartMessage": "[WARNING_SPIDERRAIN]",
                     "ZombieFallTime": 1.5
                 }
             }

    return ambush


def enlist_zombies_snowstorm(wave_points, zombie_types, wave_number, difficulty):
    """
    Same ambush as the sandstorm, but it's a snowstorm this time.
    :param wave_points: The "point" value of the current wave
    :param zombie_types: List of (zombie name, zombie point value) tuples
    :param wave_number: What wave to generate
    :param difficulty: The wave difficulty
    :return: wave, the wave dictionary formatted for PvZ2
    """

    # Sandstorms should have their own list of zombies, but I'm too lazy to make that right now

    ambush = {
        "aliases": [
            "Wave" + str(wave_number) + "StormEvent0"
        ],
        "objclass": "StormZombieSpawnerProps",
        "objdata": {
            "ColumnEnd": 7,
            "ColumnStart": 6 - difficulty_to_int(difficulty),
            "GroupSize": randint(2, 4),
            "TimeBetweenGroups": 1,
            "Type": "snowstorm",
            "WaveStartMessage": "Snowstorm!",
            "Zombies": [
            ]
        }
    }

    # Copied code from the regular function. Can probably be optimized but I'll do that later

    current_points = 0  # points "spent" on zombies this wave
    zombies_in_wave = []  # contains the zombies in this wave (name only)

    while current_points < wave_points:
        possible_zombies = []  # list of zombies that can still be added based on points left
        for zombie in zombie_types:
            if zombie[1] <= (wave_points - current_points):  # check if the zombie's point value is low enough
                possible_zombies.append(zombie)
        try:
            added_zombie = choice(possible_zombies)
        except IndexError:  # when there are no possible options (should not happen anyway since imp is hardcoded)
            added_zombie = ("tutorial_imp", 1)
        zombies_in_wave.append(added_zombie[0])
        current_points += added_zombie[1]

    # Write the zombies to the wave data
    for zombie in zombies_in_wave:
        ambush["objdata"]["Zombies"].append({"Type": "RTID(" + zombie + "@ZombieTypes)"})

    return ambush



if __name__ == "__main__":
    # Create game window
    root = Tk()
    root.title("PvZ2 Level Generator by Jerry Cui")

    main_menu()

    root.mainloop()
