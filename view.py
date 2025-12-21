import csv

def export_model_to_csv(model, T, N, filename="chicken_solution.csv"):
    """
    Exports the SAT model to a CSV file using SEMICOLON (;) delimiter.
    This format is often better for Excel in European regions.
    """
    with open(filename, mode='w', newline='') as file:
        # FIX: Use delimiter=';' so columns are separated by semicolons
        writer = csv.writer(file, delimiter=';')
        
        # Write Header
        writer.writerow(["Time", "Boat At", "Action", "Passengers", "Duration", "Arrival T", "Chickens @ A", "Chickens @ B"])

        for t in range(T + 1):
            # 1. Boat Location
            side_val = model.get(('side', t), None)
            if side_val is True: boat_loc = "Bank A"
            elif side_val is False: boat_loc = "Bank B"
            else: boat_loc = "?"

            # 2. Chickens Location
            at_A = []
            at_B = []
            for p in range(1, N + 1):
                b_val = model.get(('B', p, t), None)
                if b_val is True:
                    at_B.append(str(p))
                elif b_val is False:
                    at_A.append(str(p))
            
            # 3. Departures
            passengers = []
            direction = ""
            for p in range(1, N + 1):
                if model.get(('dep', t, p, 'a')):
                    passengers.append(str(p))
                    direction = "Depart A->B"
                elif model.get(('dep', t, p, 'r')):
                    passengers.append(str(p))
                    direction = "Depart B->A"

            # 4. Durations
            active_durs = []
            for key, val in model.items():
                if val and isinstance(key, tuple) and key[0] == 'dur' and key[1] == t:
                    active_durs.append(str(key[2]))
            
            # Join durations with comma (inside the cell)
            dur_str = ", ".join(active_durs) if active_durs else "-"
            
            # Calculate Arrival
            arr_str = "-"
            if active_durs:
                arrs = [str(t + int(d)) for d in active_durs]
                arr_str = ", ".join(arrs)

            # Write Row
            # Passengers are joined by commas within the cell: "1, 2"
            writer.writerow([
                t, 
                boat_loc, 
                direction if passengers else "Wait", 
                ", ".join(passengers) if passengers else "-", 
                dur_str, 
                arr_str,
                " ".join(at_A), # Space separated: "1 2 3"
                " ".join(at_B)
            ])
            
    print(f"\n[INFO] Solution exported to {filename} with ';' delimiter.")