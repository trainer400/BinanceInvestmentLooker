import os


class LoggableObject:
    def getCSVString(self) -> str:
        result = ""

        # Gather all the possible attributes of the polymorphism class
        variables = vars(self.__class__)
        for var in variables:
            if not callable(getattr(self, var)) and not var.startswith("__"):
                # Add the field into the result
                content = vars(self)
                result += str(content[str(var)]) + ","

        # Exclude the last coma
        result = result[0: len(result) - 1]
        result += "\n"

        return result

    def getCSVHeader(self) -> str:
        result = ""

        # Gather all the possible attributes of the polymorphism class
        variables = vars(self.__class__)
        for var in variables:
            if not callable(getattr(self, var)) and not var.startswith("__"):
                # Add the field into the result
                result += str(var) + ","

        # Exclude the last coma
        result = result[0: len(result) - 1]
        result += "\n"

        return result


def log_data(path: str, object: LoggableObject):
    # Open the file and, if necessary create it
    file = open(path, "a")

    # Check if file is empty
    if os.stat(path).st_size == 0:
        # Write the header
        file.write(object.getCSVHeader())
        print("[INFO] Created new log file: " + path)

    file.write(object.getCSVString())
    file.close()
