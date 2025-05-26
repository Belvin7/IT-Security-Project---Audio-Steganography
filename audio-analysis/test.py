import json


with open("IT-Security-Project---Audio-Steganography/audio-analysis/mp3_structureanalysis_src/output/belvin-phone-stegoaa.json") as fp:
    analysis = json.load(fp)

structure = analysis.get("structure", {})
mpeg_frame_data = structure.get("mpeg_frame_data", [])

input("$ header-position")
c1 = 0
for i, frame in enumerate(mpeg_frame_data):
    if i == len(mpeg_frame_data) - 1:
        break
    position = frame["position"]
    length = frame["length"]
    next_position = mpeg_frame_data[i + 1]["position"]
    if (position + length != next_position):
        print(i, position, length, next_position, end=" | ")
        c1 += 1
print("End.")
print(f"{c1} found.")
print()

input("$ header-position-value")
c2 = 0
for i, frame in enumerate(mpeg_frame_data):
    if frame["length"] - frame["side_info"]["length"] - frame["main_data"]["length"] != 4:
        print(i, frame["length"], frame["side_info"]["length"], frame["main_data"]["length"], end=" | ")
        c2 += 1
print("End.")
print(f"{c2} found.")
print()

input("$ 1000 < part2_3 < 1400")
c3_1 = 0
c3_2 = 0
for i, frame in enumerate(mpeg_frame_data):
    frame_found = False
    for j, granule in enumerate(frame["side_info"]["granule_info"]):
        for length in granule["part2_3_length"]:
            if 1000 < length < 1400:
                print(f"({i}, {j})", length, end=" | ")
                c3_1 += 1
                frame_found = True
    if frame_found:
        c3_2 += 1

print("End.")
print(f"{c3_1} found, in {c3_2} frames.")
