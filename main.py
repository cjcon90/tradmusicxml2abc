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


@dataclasses.dataclass
class Tune:
    time_signature: TimeSignature
    key: Key
    measures: t.List[Measure]

    def as_str(self) -> str:
        tune_str: str = ""
        tune_str += f"Time Signature: {self.time_signature.as_str()}\n"
        tune_str += f"Key: {self.key.as_str()}\n"
        count: float = 0
        for measure in self.measures:
            if ending := measure.ending:
                tune_str += f"{ending}) "
            count = 0
            for note in measure.notes:
                length = note.duration + 0.5 if note.dotted else note.duration
                mid_point = (
                    self.time_signature.upper
                    if self.time_signature.lower <= 4
                    else int(self.time_signature.upper / 2)
                )
                if count > 0 and count <= mid_point and count + length > mid_point:
                    tune_str += " "
                count += length
                tune_str += note.value
                if note.high:
                    tune_str += "'"
                if note.low:
                    tune_str += ","
                if length > 1:
                    tune_str += "- "
            if measure.part_ending:
                tune_str += " ||\n"
            elif measure.repeat:
                tune_str += " :| "
            elif int(measure.number) < len(self.measures):
                tune_str += " | "
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
        measures.append(
            Measure(
                number=number,
                notes=notes,
                ending=ending_num,
                part=part,
                part_ending=part_ending,
                repeat=repeat,
            )
        )
        if part_ending:
            part += 1

    tune = Tune(time_signature=time_signature, key=key, measures=measures)
    tune_str = tune.as_str()
    with open("/tmp/measure_data", "w") as f:
        f.write(json.dumps(measure_data, indent=2))
    print(tune_str)


if __name__ == "__main__":
    main()
