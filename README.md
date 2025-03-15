# LINUX ONLY. IF YOU ARE NOT USING LINUX, THEN START DOING IT RIGHT NOW.

## Usage

```sh
# Clone the repo and install dependencies
git clone https://github.com/wzrayyy-university/dsa-cli sort-me
cd sort-me
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the program
python3 main.py
# You will be asked for login details, only telegram based authorization works.
# Let's create an alias to make this example simpler
alias sm="$(readlink -e ./main.py)"

# Read the help message (usually this helps)
sm --help

# You can also read what arguments a specified subcommand requires with --help
sm init --help

# After you have logged in, `cd` to your contest folder and run
sm init "CONTEST_ID"
# `CONTEST_ID` is taken from the url:
# https://sort-me.org/contest/301
# Here, CONTEST_ID is going to be 301

# You will see a new file appear named `.sortme.json`. Don't delete this file. It contains all the information for the current contest, as well as the example tests provided in the task description.
# Now, create a file named `a.cpp` (case insensitive) and solve the task!
# !IMPORTANT! Task name MUST be in format \w.cpp, i.e. if you are solving a task `A`, you MUST name the file `a.cpp`.
# You can read the task by running
sm info a

# After you have solved the task `A`, you can test it with
sm test a.cpp

# If (and only if 🙂) the tests pass, you can submit your solution with
sm push a.cpp
```
