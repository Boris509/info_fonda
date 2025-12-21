import csv

def export_model_to_csv(model, T, N, filename="chicken_solution.csv"):

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file, delimiter=";")

        # EXACT header (11 columns)
        writer.writerow([
            "Time",
            "Boat",
            "Action",
            "Direction",
            "Passengers",
            "Duration",
            "Arrival T",
            "# Chickens A",
            "Chickens at A",
            "# Chickens B",
            "Chickens at B"
        ])

        for t in range(T + 1):

            # Boat
            side = model.get(("side", t))
            boat = "Bank A" if side is True else "Bank B" if side is False else ""

            # Chickens
            at_A, at_B = [], []
            for p in range(1, N + 1):
                v = model.get(("B", p, t))
                if v is True:
                    at_B.append(str(p))
                elif v is False:
                    at_A.append(str(p))

            # Move
            passengers = []
            direction = ""
            for p in range(1, N + 1):
                if model.get(("dep", t, p, "a")):
                    passengers.append(str(p))
                    direction = "A → B"
                elif model.get(("dep", t, p, "r")):
                    passengers.append(str(p))
                    direction = "B → A"

            action = "Move" if passengers else "Wait"

            # Duration
            durations = [
                str(k[2]) for k, v in model.items()
                if v and isinstance(k, tuple) and k[0] == "dur" and k[1] == t
            ]

            dur_str = ", ".join(durations) if durations else ""
            arr_str = ", ".join(str(t + int(d)) for d in durations) if durations else ""

            # 🔒 ALWAYS 11 CELLS
            writer.writerow([
                t,
                boat,
                action,
                direction,
                ", ".join(passengers) if passengers else "",
                dur_str,
                arr_str,
                len(at_A),
                " ".join(at_A),
                len(at_B),
                " ".join(at_B)
            ])

    print(f"[INFO] Excel-perfect grid exported to {filename}")
