def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog="Jmail",
        description="Super-charged Gmail.",
        epilog="Thank you for using Jmail.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "-a", "--arg_1", type=str,
        help="Configuration path."
    )
    parser.add_argument(
        "-b", "--arg_2", type=str,
        help="Configuration path."
    )
    args = parser.parse_args()   
    return args


inputs = parse_args()

a = inputs.arg_1
b = inputs.arg_2

print("arg_1: ", a)
print("arg_2: ", b)
