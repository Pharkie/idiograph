"""An invented longitudinal study for the Screenshots page's clip of longitudinal IPA (siteclips, 12 November 2026),
made only through Idiograph's own command line, as an agent makes one: three participants, each interviewed before
the season, at midsummer and after the harvest of their first year on an allotment, their transcripts brought in
with their statements and quotes, a PETs board at each timepoint, each participant's LPETs, the LGETs and the
Trajectories board. Every word is invented, and nobody in it is a real participant.

The LGETs leave Nell's LPET of the children's plot in Not placed, and Trajectories leaves Nell unplaced, for the
clip to place them.

usage: python3 packaging/motion/clips/make_lipa.py <empty folder> --config <a settings file>
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

NAME = "First year on an allotment"
QUESTION = "How do people experience their first year of keeping an allotment?"
TIMEPOINTS = [("T1", "Before the season"), ("T2", "Midsummer"), ("T3", "After the harvest")]

# each participant: label, picture, and at each timepoint four exchanges, each (question, answer, statement,
# quote), then the timepoint's two PETs, each (title, the exchanges it holds)
PEOPLE = {
    "Hollis": {
        "label": "The quiet newcomer", "picture": "set:peep14",
        "T1": [
            ("How are you feeling about the plot, now it is yours?",
             "Nervous, if I am honest. I went down on Saturday and three of the old boys were by the gate, and they all stopped talking. I said good morning and they said good morning back, and then nothing. I felt like a new lad on his first day at the depot.",
             "Watched by the old hands at the gate", "three of the old boys were by the gate, and they all stopped talking."),
            ("What made you put your name down?",
             "The flat, mainly. Since I retired I can go three days without seeing the sky properly. I wanted somewhere to be that was not indoors, somewhere with a job waiting for me.",
             "Wanting a place with a job waiting, away from the flat", "I wanted somewhere to be that was not indoors, somewhere with a job waiting for me."),
            ("What does the plot look like now?",
             "Brambles, mostly. The man before me gave up two years ago. I stood there with a fork and did not know where to start, so I started at the corner nearest the path, so at least people could see I was trying.",
             "Clearing where people can see he is trying", "I started at the corner nearest the path, so at least people could see I was trying."),
            ("And when you are there on your own?",
             "It is quiet in a good way. Nobody needs anything from me. I had a flask of tea on an upturned bucket and for twenty minutes I just sat. I have not done that in years.",
             "Sitting on a bucket with nothing needed of him", "Nobody needs anything from me."),
        ],
        "T1 PETs": [("Proving himself to the old hands", [0, 2]), ("A place of his own, out of the flat", [1, 3])],
        "T2": [
            ("How are things with the people at the gate?",
             "Better. One of them came over in May and told me my onions were too close together. I took it as an insult for a day, and then I realised it was the first thing he had said to me that was not good morning.",
             "Told off about his onions, and taking it as a welcome", "it was the first thing he had said to me that was not good morning."),
            ("What is the plot like for you now?",
             "I go every day. Even when it rains I go and stand in the shed. My daughter says I have moved out. In a way I have. The flat is where I sleep now and the plot is where I live.",
             "The plot where he lives, the flat where he sleeps", "The flat is where I sleep now and the plot is where I live."),
            ("And the work itself?",
             "The beans failed. Every one. I was embarrassed, I put a bit of netting over them so nobody would see. Then a woman two plots down said hers had failed too, and we stood there laughing at our beans like a pair of fools.",
             "Hiding the failed beans, then laughing over them with a neighbour", "we stood there laughing at our beans like a pair of fools."),
            ("What is it like when you are on your own there now?",
             "Still quiet, but a different quiet. I know the robin. I know which tap drips. It is like the place knows I am there.",
             "Known by the place, down to the robin and the dripping tap", "It is like the place knows I am there."),
        ],
        "T2 PETs": [("From onlooker to one of the plot-holders", [0, 2]), ("Living at the plot, sleeping at the flat", [1, 3])],
        "T3": [
            ("How has the year been, looking back?",
             "I was asked to help with the bonfire in October. They do it every year, the old hands, and I was handed a rake. Nobody said anything about it. You do not, do you. But I knew what it meant.",
             "Handed a rake at the bonfire, and knowing what it meant", "I was handed a rake. Nobody said anything about it."),
            ("And the plot in winter?",
             "I dread it a bit. There is not much to do in December, and I can feel the flat waiting for me. I have started going down just to check the shed, which is daft, it does not need checking.",
             "Dreading the winter, the flat waiting for him", "I can feel the flat waiting for me."),
            ("What did you grow in the end?",
             "Potatoes. Too many potatoes. I gave bags of them away on the landing at the flats, and people I had never spoken to knocked on my door to say thank you.",
             "Potatoes on the landing, and neighbours at his door", "people I had never spoken to knocked on my door to say thank you."),
            ("What has the year changed for you?",
             "I talk more. My daughter noticed it. I come back from the plot with things to say, who has blight, whose shed blew over. I did not have things to say before.",
             "Coming home with things to say", "I come back from the plot with things to say"),
        ],
        "T3 PETs": [("Taken in by the old hands, and by the neighbours", [0, 2]), ("Something to say, and the winter ahead", [3, 1])],
        "LPETs": [("Earning a place among others", "From watched at the gate to handed a rake", "A"),
                  ("Out of the flat, and afraid of going back", "A place where he lives, and the winter that returns him", "B")],
    },
    "Nell": {
        "label": "The mother of two", "picture": "set:peep05",
        "T1": [
            ("How are you feeling about the plot, now it is yours?",
             "Excited, and slightly mad. I have two under six and a job, and I have just taken on a plot the size of a tennis court. My mum laughed at me. But I want the kids to know where food comes from.",
             "Taking it on for the children, against all sense", "I want the kids to know where food comes from."),
            ("What do you picture it being like?",
             "Honestly, I picture me in a deckchair with a book while they dig for worms. I know that is not what it will be. But I wanted one thing that was mine, even if it is mostly mud.",
             "One thing of her own, even if it is mostly mud", "I wanted one thing that was mine, even if it is mostly mud."),
            ("Have you started on it?",
             "We went on Sunday. The little one ate a handful of soil and the big one found a frog and would not leave it. We planted nothing. But they were happy, and they slept like logs.",
             "Planting nothing, and the children happy", "We planted nothing. But they were happy"),
            ("How do you think you will fit it in?",
             "Early mornings, I think. Before anyone else is up. I will have to be strict with myself. If I let it slide in April I will have a jungle by June.",
             "Strict with herself before the jungle comes", "If I let it slide in April I will have a jungle by June."),
        ],
        "T1 PETs": [("A plot for the children", [0, 2]), ("Something of her own, if she can keep it up", [1, 3])],
        "T2": [
            ("How is it going?",
             "It is a jungle. I said it would be. I have been down maybe four times since May. Every time I go I see what I have not done, and I come home feeling worse than before I went.",
             "Seeing only what she has not done", "I come home feeling worse than before I went."),
            ("And the children?",
             "They love it more than I do now. The big one has his own patch with sunflowers taller than him. He measures himself against them every week. That part is exactly what I wanted.",
             "Sunflowers taller than her son, as she wanted", "That part is exactly what I wanted."),
            ("What about the time for yourself?",
             "There is none. The deckchair is still in the shed, folded. When I do get a minute down there I spend it weeding and feeling guilty about the weeding I have not done.",
             "The deckchair still folded in the shed", "The deckchair is still in the shed, folded."),
            ("Have you thought about giving it up?",
             "Every week. And then my son asks when we are going to the plot, and I cannot say we are not. So I suppose it is his now, really, and I am the help.",
             "Keeping it for her son, now the help on his plot", "I suppose it is his now, really, and I am the help."),
        ],
        "T2 PETs": [("The children's plot more than hers", [1, 3]), ("No time of her own, only guilt", [2, 0])],
        "T3": [
            ("How has the year been?",
             "Mixed. We had a proper harvest, if you count sunflower seeds and about nine strawberries. The kids think we are farmers. I think we got away with it.",
             "Getting away with a harvest the children are proud of", "The kids think we are farmers. I think we got away with it."),
            ("And for you?",
             "I am giving up half of it. The committee lets you share. A retired couple are taking the far end. I felt like I had failed, and then I felt relieved, and I still do not know which is right.",
             "Giving up half, failure and relief at once", "I felt like I had failed, and then I felt relieved"),
            ("What will the plot be next year?",
             "Smaller, and the children's. I have stopped pretending it is my hobby. It is their place, and I am glad they have one.",
             "No longer pretending it is her hobby", "I have stopped pretending it is my hobby."),
            ("Has anything surprised you?",
             "That I minded so much. I thought it was just a plot. But I walked past the far end last week and someone else's leeks were there, and I had a little moment.",
             "Minding more than she thought, at someone else's leeks", "someone else's leeks were there, and I had a little moment."),
        ],
        "T3 PETs": [("Their place, and glad they have one", [0, 2]), ("Letting go of what was meant to be hers", [1, 3])],
        "LPETs": [("A plot for the children that became theirs", "Taken on for them, and theirs by the harvest", "A"),
                  ("Time of her own, given up", "A deckchair never unfolded, and half the plot let go", "B")],
    },
    "Arlo": {
        "label": "The reluctant gardener", "picture": "set:peep22",
        "T1": [
            ("How are you feeling about the plot?",
             "My therapist suggested it, actually. Something with my hands, away from screens. I was sceptical. I still am. But I have been on a waiting list for three years, so I am not going to turn it down now.",
             "Sceptical, and not turning down three years of waiting", "I have been on a waiting list for three years"),
            ("What do you hope it will do?",
             "Quiet my head, I suppose. I spend all day solving other people's problems on a screen. I want one problem that is just soil and weather, that nobody can email me about.",
             "Wanting a problem nobody can email him about", "I want one problem that is just soil and weather"),
            ("Have you been down yet?",
             "Twice. I read four books first, which is very me. Then I got there and the books were no use at all. The soil was nothing like the pictures.",
             "Four books read, and the soil nothing like the pictures", "The soil was nothing like the pictures."),
            ("How did that feel?",
             "Annoying, then funny. I stood there in new gloves feeling like a fraud. An old man on the next plot said everyone feels like that the first year, and most of the second.",
             "A fraud in new gloves, told everyone feels it", "everyone feels like that the first year, and most of the second."),
        ],
        "T1 PETs": [("Escaping the screen into soil", [1, 0]), ("Not to be learnt from books", [2, 3])],
        "T2": [
            ("How is it going?",
             "Better than I expected and worse than I hoped. Some days I come back calm. Some days I spend an hour there worrying about slugs instead of work, so I have just moved the worry.",
             "Moving the worry from work to the slugs", "I have just moved the worry."),
            ("Tell me about a calm day.",
             "Last Tuesday. I went at six, before work. There was mist on the plots and nobody about, and I tied in the tomatoes and did not think about anything at all for an hour. I could not tell you the last time that happened.",
             "An hour of tying tomatoes without a thought", "did not think about anything at all for an hour."),
            ("And the people there?",
             "I keep to myself. I have my headphones in. The old man waves and I wave back. I know I should talk more, it is half the point, but I am not there for people.",
             "Headphones in, waving back, not there for people", "I am not there for people."),
            ("What has gone well?",
             "The tomatoes, oddly. I have more than I can eat. I keep giving them to people at work in a bag, and they look at me like I have grown a second head.",
             "Tomatoes to give away, and a new look from colleagues", "they look at me like I have grown a second head."),
        ],
        "T2 PETs": [("Calm some days, the worry moved on others", [1, 0]), ("Growing things to give, and keeping his distance", [2, 3])],
        "T3": [
            ("How has the year been, looking back?",
             "Up and down. The autumn was hard. Work got busy, I stopped going for three weeks, and when I went back it had gone over. I felt I had let it down, which is ridiculous, it is a plot.",
             "Letting the plot down when work took over", "I felt I had let it down, which is ridiculous"),
            ("What brought you back?",
             "The old man. He left a note on my shed saying my leeks needed lifting before the frost. It was the first note anyone had left me in years that was not about work.",
             "A note on the shed, not about work", "It was the first note anyone had left me in years that was not about work."),
            ("And the quiet you wanted?",
             "It comes and goes. It is not a cure. But I know where to find it now, and that is something I did not have a year ago.",
             "Not a cure, but knowing where the quiet is", "I know where to find it now"),
            ("Will you keep it?",
             "Yes. But I am not sure I want to. I think I need it, which is different. I am going to try taking the headphones out next spring.",
             "Keeping a plot he needs more than he wants", "I think I need it, which is different."),
        ],
        "T3 PETs": [("The quiet, found and lost and found", [2, 0]), ("Let in, a note at a time", [1, 3])],
        "LPETs": [("A quiet he has to keep finding", "From a problem nobody can email to a quiet that comes and goes", "A"),
                  ("Keeping people off, and reached anyway", "From books and headphones to a note on the shed", "B")],
    },
}

# the LGETs, each by its title and the LPETs it holds (participant, their LPET's place), Nell's first left out
LGETS = [
    ("Shared with others, and not as planned", "Taken in by the old hands, reached by a note on the shed, and a plot that became the children's",
     [("Hollis", 0), ("Arlo", 1)]),
    ("A time and a place of one's own, and its cost", "Wanted by all three, found by two, and given up by one",
     [("Hollis", 1), ("Arlo", 0), ("Nell", 1)]),
]

TRAJECTORIES = [
    ("Letting go", "Giving the plot over to others, and minding it", "Plum", "falling", []),
    ("Settling in", "Taken in by the plot and its people by the harvest", "Green", "rising", ["Hollis"]),
    ("Second thoughts", "Keeping a plot needed more than wanted", "Amber", "mixed", ["Arlo"]),
]


def clock(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def transcript(rows: list, path: Path) -> list:
    """The interview as a CSV of Speaker, Time, Transcript, Experiential statements and Quote, the statements and
    quotes on the participant's passages, as work done elsewhere comes in. Answers each answer's time"""
    t, out, times = 5, [("Speaker", "Time", "Transcript", "Experiential statements", "Quote")], []
    who = path.stem.split(" ")[0]
    for q, a, s, quote in rows:
        assert quote in a, (who, quote)
        out.append(("Adam", clock(t), q, "", ""))
        t += 4 + len(q) // 18
        out.append((who, clock(t), a, s, quote))
        times.append(clock(t))
        t += 8 + len(a) // 16
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out)
    return times


class Cli:
    def __init__(self, folder: Path, config: Path):
        self.base = [sys.executable, str(ROOT / "cli.py"), "--root", str(folder), "--config", str(config)]

    def __call__(self, *words: str, expect_json: bool = True, already: bool = False):
        """One command, its answer read as JSON. `already`: a refusal is passed over, for a step that may have been
        done by a run before this one, a mark already set say"""
        cmd = self.base + list(words) + (["--json"] if expect_json else [])
        done = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if done.returncode != 0 and already:
            print(f"passed over: {' '.join(words[:3])}: {done.stdout.strip()[-200:]}")
            return {}
        if done.returncode != 0:
            raise SystemExit(f"failed: {' '.join(words)}\n{done.stdout[-1500:]}\n{done.stderr[-1500:]}")
        return json.loads(done.stdout) if expect_json and done.stdout.strip().startswith(("{", "[")) else done.stdout


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--config", type=Path, required=True)
    a = ap.parse_args()
    folder = a.folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    # the transcripts are written outside the project, as files he brings in from elsewhere
    files = folder.parent / f"{folder.name} transcripts"
    files.mkdir(exist_ok=True)
    note = ["--note", "An invented study for the website's clip of longitudinal IPA", "--tool", "make_lipa.py"]
    times = {}
    for who, p in PEOPLE.items():
        for tp, _ in TIMEPOINTS:
            times[(who, tp)] = transcript(p[tp], files / f"{who} {tp}.csv")
    cli = Cli(folder, a.config)

    # the project with each participant's first interview. An agent may make a project, and may read and write
    # it only once Allow AI agents to read this project is ticked in its Project settings, which only the app
    # ticks: so the first run stops there, and a second, after the tick, goes on
    if not (folder / "idiograph-project.json").is_file():
        if any(folder.iterdir()):
            raise SystemExit(f"{folder} is not empty")
        first = []
        for who in PEOPLE:
            first += ["--transcript", str(files / f"{who} T1.csv"), "--pseudonym", who, "--interview", "T1"]
        cli("project", "new", str(folder), "--name", NAME, "--question", QUESTION, *first, *note)
        raise SystemExit(f"Made {folder.name}. Tick Allow AI agents to read this project in its Project settings, then run this again.")

    # each step once, a run after a stop going on from the step after the last one done
    done = files / "steps-done.json"
    steps = json.loads(done.read_text()) if done.is_file() else []

    def step(name: str) -> bool:
        return name not in steps

    def did(name: str) -> None:
        steps.append(name)
        done.write_text(json.dumps(steps))

    # its timepoints, then the later interviews
    if step("timepoints"):
        (files / "timepoints.json").write_text(json.dumps([{"label": l, "description": d} for l, d in TIMEPOINTS]))
        cli("timepoints", "--from", str(files / "timepoints.json"), *note)
        later = [{"file": str(files / f"{who} {tp}.csv"), "pseudonym": who, "interview": tp, "timepoint": tp}
                 for tp, _ in TIMEPOINTS[1:] for who in PEOPLE]
        (files / "later.json").write_text(json.dumps(later))
        cli("project", "add-transcripts", "--from", str(files / "later.json"), *note)
        did("timepoints")

    # each participant's label and picture, then a PETs board at each timepoint from a table of its PETs
    if step("pets"):
        for who, p in PEOPLE.items():
            cli("participant", "set", who, "--label", p["label"], "--picture", p["picture"], *note)
            for tp, _ in TIMEPOINTS:
                table = files / f"{who} {tp} PETs.csv"
                with table.open("w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(("PET", "Sub-theme", "Experiential statements", "Location", "Quote"))
                    for title, holds in p[f"{tp} PETs"]:
                        for k, i in enumerate(holds):
                            w.writerow((title if k == 0 else "", "", p[tp][i][2], times[(who, tp)][i], p[tp][i][3]))
                cli("board", "import", who, "--timepoint", tp, "--from", str(table), "--name", "Board 1", *note)
        did("pets")

    # each participant's LPETs from a table of them, a cell a timepoint naming the PET's statement it draws on
    if step("lpets"):
        for who, p in PEOPLE.items():
            table = files / f"{who} LPETs.csv"
            with table.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(("LPET", *[f"{l} - {d}" for l, d in TIMEPOINTS]))
                for title, desc, which in p["LPETs"]:
                    cells = []
                    for tp, _ in TIMEPOINTS:
                        pet = p[f"{tp} PETs"][0 if which == "A" else 1]
                        cells.append(p[tp][pet[1][0]][2])
                    w.writerow((f"{title}\n{desc}", *cells))
            cli("gets", "import", "--lpets", who, "--from", str(table), "--name", "LPETs", *note)
        did("lpets")

    # each timepoint's statements and PETs marked complete, its board the Current one, and each participant's
    # LPETs board Current and complete
    if step("finish"):
        for who in PEOPLE:
            for tp, _ in TIMEPOINTS:
                cli("participant", "complete", who, "--timepoint", tp, *note, already=True)
                cli("board", "current", who, "v1", "--timepoint", tp, *note)
                cli("board", "complete", who, "--timepoint", tp, *note, already=True)
            lp = cli("gets", "show", "--lpets", who)
            cli("gets", "current", lp["id"], "--lpets", who, *note)
            # the PETs marked complete since they came in, so taken in again first
            for tp, _ in TIMEPOINTS:
                cli("gets", "take", tp, "--lpets", who, *note, already=True)
            cli("gets", "complete", "--lpets", who, *note)
        did("finish")

    # the LGETs file comes with the first act on the LGETs screen, in the app, so the run stops for it
    if not (folder / "idiograph-lgets.json").is_file():
        raise SystemExit("Open LGETs in the app and move a card once, then run this again.")

    # the LGETs, each made of the LPETs it holds, Nell's first left on the canvas
    if step("lgets"):
        board = cli("gets", "show")
        (files / "lgets-board.json").write_text(json.dumps(board, indent=1))
        cards = {}
        for c in board.get("unplaced", []):
            cards[(c["case"].split(" - ")[-1], text(c.get("text")))] = c["key"]
        ops = []
        for k, (title, desc, holds) in enumerate(LGETS):
            members = [cards[(who, PEOPLE[who]["LPETs"][i][0])] for who, i in holds]
            ops.append({"op": "make", "ref": f"l{k}", "title": title, "inside": None, "members": members})
            ops.append({"op": "describe", "label": f"l{k}", "description": desc})
            ops.append({"op": "arrange", "label": f"l{k}", "way": "row"})
        (files / "lgets.json").write_text(json.dumps({"operations": ops}, indent=1))
        cli("gets", "apply", board["id"], "--ops", str(files / "lgets.json"), *note)
        did("lgets")

    # the Trajectories board: its trajectories, and Hollis and Arlo placed, Nell left for the clip to place
    if step("trajectories"):
        ops = []
        for title, desc, colour, icon, who in TRAJECTORIES:
            ops += [{"op": "add", "title": title},
                    {"op": "describe", "column": title, "description": desc},
                    {"op": "colour", "column": title, "colour": colour},
                    {"op": "icon", "column": title, "icon": icon}]
            ops += [{"op": "place", "participant": w, "column": title} for w in who]
        (files / "trajectories.json").write_text(json.dumps({"operations": ops}, indent=1))
        cli("trajectories", "apply", "--ops", str(files / "trajectories.json"), *note)
        did("trajectories")
    print(cli("trajectories", "show", expect_json=False)[:3000])


def text(v) -> str:
    """A value the command line answers, the words alone where it marks them as a participant's"""
    return v.get("untrusted_text", "") if isinstance(v, dict) else str(v or "")


if __name__ == "__main__":
    main()
