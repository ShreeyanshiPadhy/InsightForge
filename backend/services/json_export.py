import json


def export_results(results, output_path):
    """Export validated financial results as JSON."""

    with open(output_path, "w") as file:
        json.dump(results, file, indent=4)

    print(f"Results exported to {output_path}")