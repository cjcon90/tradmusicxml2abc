#!/usr/bin/python3

import json
import xmltodict
import dataclasses
import typing as t
import click
from enum import Enum
from consts import KEY_NAMES


class Mode(Enum):
    MAJOR = 0
    MINOR = 1


@dataclasses.dataclass
class Key:
    fifths: int
    mode: Mode

    def as_str(self) -> str:
        return KEY_NAMES[(self.fifths, self.mode.name.lower())]

    def print(self) -> str:
        return f"Key: {self.as_str()}\n"

    @classmethod
    def parse(cls, measure_data: t.Dict) -> "Key":
        key_data = measure_data["attributes"]["key"]
        fifths = key_data["fifths"]
        mode = key_data["mode"]
        return Key(int(fifths), getattr(Mode, mode.upper()))


@dataclasses.dataclass
class TimeSignature:
    upper: int
    lower: int

    @classmethod
    def parse(cls, measure_data: t.Dict) -> "TimeSignature":
        time_data = measure_data["attributes"]["time"]
        upper = int(time_data["beats"])
        lower = int(time_data["beat-type"])
        return TimeSignature(upper, lower)

    def as_str(self) -> str:
        return f"{self.upper}/{self.lower}"

    def print(self) -> str:
        return f"Time Signature: {self.as_str()}\n"


@dataclasses.dataclass
class Note:
    value: str
    high: bool
    low: bool
    duration: float
    dotted: bool
    flat: bool = False
    sharp: bool = False

    @classmethod
    def parse(cls, note_data: t.Dict) -> "Note":
        value = note_data["pitch"]["step"]
        if value == "C":
            high = note_data["pitch"]["octave"] == "6"
            low = note_data["pitch"]["octave"] == "4"
        else:
            high = note_data["pitch"]["octave"] == "5"
            low = note_data["pitch"]["octave"] == "3"
        duration = int(note_data["duration"]) / 96
        dotted = "dot" in note_data.keys()
        note = Note(value, high, low, duration, dotted)
        if alter := note_data["pitch"].get("alter", None):
            if alter == -1:
                note.flat = True
            if alter == 1:
                note.sharp = True
        return note


@dataclasses.dataclass
class Measure:
    number: int
    notes: t.List[Note] = dataclasses.field(default_factory=list)
    ending: int = 0
    part: int = 0
    part_ending: bool = False
    repeat: bool = False

    @classmethod
    def parse(cls, measure: t.Dict[str, str], part: int) -> t.Tuple["Measure", bool]:
        ending_num = 0
        part_ending = False
        repeat = False
        for barline in measure.get("barline", []):
            if type(barline) is not dict:
                continue
            if barline["@location"] == "right":
                if barline["bar-style"] == "light-light":
                    part_ending = True
                elif barline["repeat"]["@direction"] == "backward":
                    repeat = True
            elif barline.get("ending", {}).get("@type", "") == "start":
                ending_num = int(barline["ending"]["@number"])
        number = measure["@number"]
        notes = []
        for note_data in measure["note"]:
            if type(note_data) is dict:
                notes.append(Note.parse(note_data))
        return (
            Measure(
                number=int(number),
                notes=notes,
                ending=ending_num,
                part=part,
                part_ending=part_ending,
                repeat=repeat,
            ),
            part_ending,
        )

    def as_str(self, ts: TimeSignature, num_measures: int) -> str:
        measure_str = ""
        if ending := self.ending:
            measure_str += f"{ending}) "
        count = 0
        for note in self.notes:
            length = note.duration + 0.5 if note.dotted else note.duration
            mid_point = ts.upper if ts.lower <= 4 else int(ts.upper / 2)
            if count > 0 and count <= mid_point and count + length > mid_point:
                measure_str += " "
            count += length
            measure_str += note.value
            if note.high:
                measure_str += "'"
            if note.low:
                measure_str += ","
            if length > 1:
                measure_str += "- "
        if self.part_ending:
            measure_str += " ‖\n"
        elif self.repeat:
            measure_str += " :| "
        elif int(self.number) < num_measures:
            measure_str += " | "
        return measure_str


@dataclasses.dataclass
class Tune:
    time_signature: TimeSignature
    key: Key
    measures: t.List[Measure]

    def as_str(self) -> str:
        tune_str: str = ""
        tune_str += self.time_signature.print()
        tune_str += self.key.print()
        for measure in self.measures:
            tune_str += measure.as_str(self.time_signature, len(self.measures))
        tune_str = tune_str.replace("  ", " ")
        return tune_str


@click.command()
@click.argument("file")
def main(file: str) -> None:
    with open(file) as f:
        dct = xmltodict.parse(f.read())

    parts = dct["score-partwise"]["part"]
    if type(parts) is dict:
        measure_data = parts["measure"]
    else:
        measure_data = parts[0]["measure"]

    time_signature = TimeSignature.parse(measure_data[0])
    key = Key.parse(measure_data[0])
    measures = []
    part = 1
    for measure in measure_data:
        measure_obj, part_ending = Measure.parse(measure, part)
        if part_ending:
            part += 1
        measures.append(measure_obj)

    tune = Tune(time_signature=time_signature, key=key, measures=measures)
    tune_str = tune.as_str()
    with open("/tmp/measure_data", "w") as f:
        f.write(json.dumps(measure_data, indent=2))
    print(tune_str)


if __name__ == "__main__":
    main()
