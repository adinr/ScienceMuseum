import tkinter
import tkinter.ttk
import pywhatkit
import csv
import argparse
import os
import sys
import logging


class Guide:
    def __init__(self, name, number):
        self.name = name
        self.number = f"+972{number[1:].replace('-', '')}"
        self.var = tkinter.IntVar(value=0)

class MessageSender:
    def __init__(self):
        self.parse_args()
        logging.basicConfig(stream=sys.stderr)
        self.logger = logging.getLogger("MessageSender")
        self.logger.setLevel(logging.DEBUG if self.args.verbose else logging.INFO)
        self.build_form()

    def parse_args(self):
        parser = argparse.ArgumentParser(
            prog="MessageSender",
            description="Sends WhatsApp messages in bulk",
        )
        parser.add_argument("-d", "--dry", action="store_true", help="Don't actually send messages")
        parser.add_argument("-t", "--test", help="Additional test numbers (format: <name>:<number>[<name>:<number>...])")
        parser.add_argument("-v", "--verbose", action="store_true", help="print debug logs")
        self.args = parser.parse_args()

    def build_form(self):
        NUM_COLUMNS = 3

        self.root = tkinter.Tk()
        self.root.title("מי פנוי באלנבי?")
        self.frm = tkinter.ttk.Frame(self.root, padding=10)
        self.frm.grid()
        self.guides = get_guides(self.args.test)
        for guide in self.guides:
            self.logger.debug(f"Guide {guide.number}")
        receipt_check_boxes = []
        for i, guide in enumerate(self.guides):
            check_button = tkinter.ttk.Checkbutton(self.frm, text=guide.name, variable=guide.var)
            check_button.grid(column=(NUM_COLUMNS - i % NUM_COLUMNS - 1), row=i // NUM_COLUMNS)
            receipt_check_boxes.append(check_button)
        sessions = ["ראשון", "שני", "שלישי", "רביעי"]
        days = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
        message_templates = [
            MessageTemplate("היי, אפשרי לך לקחת מחזור {} ביום {}?", sessions, days),
            MessageTemplate("היי, הקבוצה של מחזור {} ביום {} ביטלה.", sessions, days),
            MessageTemplate("היי, הקבוצה של מחזור {} ביום {} {} ב{}. אפשרי לך?", sessions, days, ["מאחרת", "מקדימה"], ["15 דקות", "30 דקות", "שעה"]),
            MessageTemplate("תודה!")
        ]
        self.message_templates_dict = {template.template: template for template in message_templates}
        row_accumulator = Accumulator()

        INPUT_COLUMN = NUM_COLUMNS

        self.free_text_widget_var = tkinter.StringVar()
        self.free_text_widget = tkinter.ttk.Entry(self.frm, textvariable=self.free_text_widget_var, validate="key", validatecommand=(self.frm.register(self.on_free_text_updated), "%P"))
        self.free_text_widget.grid(column=INPUT_COLUMN, row=row_accumulator.get_next())

        self.message_widget_var = tkinter.StringVar()
        self.message_widget = tkinter.ttk.OptionMenu(self.frm, self.message_widget_var, None, *[template.template for template in message_templates], command=self.on_message_template_selected)
        self.message_widget.grid(column=INPUT_COLUMN, row=row_accumulator.get_next())

        self.template_vars = []
        self.var_widgets = []
        for i in range(4):
            message_template_var = tkinter.StringVar()
            var_widget = tkinter.ttk.OptionMenu(self.frm, message_template_var, command=self.on_message_var_selected)
            var_widget.grid(column=INPUT_COLUMN, row=row_accumulator.get_next())
            self.var_widgets.append(var_widget)
            self.template_vars.append(message_template_var)

        self.message_label = tkinter.ttk.Label(self.frm)
        self.message_label.grid(column=INPUT_COLUMN, row=row_accumulator.get_next())

        tkinter.ttk.Button(self.frm, text="Send", command=self.send_message).grid(column=INPUT_COLUMN, row=row_accumulator.get_next())

        tkinter.ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=INPUT_COLUMN, row=row_accumulator.get_next())

    def mainloop(self):
        self.root.mainloop()

    def get_message_text(self):
        free_text = self.free_text_widget_var.get()
        if free_text:
            message_text = free_text
        else:
            message_text = self.message_widget_var.get()
            message_text = message_text.format(*[template_var.get() for template_var in self.template_vars[:len(self.find_template_vars(message_text))]])
        self.message_label.configure(text=message_text)
        return message_text

    def send_message(self):
        message_text = self.get_message_text()
        if not message_text:
            self.logger.warn("no message")
            return
        self.logger.info(f"{'[dry run] ' if self.args.dry else ''}sending message {message_text} to")
        for guide in self.guides:
            if guide.var.get():
                self.logger.info(guide.number)
                if not self.args.dry:
                    pywhatkit.sendwhatmsg_instantly(guide.number, message_text, wait_time=20, tab_close=True)

    def find_template_vars(self, template):
        i = template.find("{}")
        vars = []
        while i >= 0:
            vars.append(i)
            i = template.find("{}", i + 1)
        return vars

    def on_message_template_selected(self, selected_message_template):
        self.logger.debug(f"on_message_template_selected {selected_message_template}")
        message_template = self.message_templates_dict[selected_message_template]
        var_indices = self.find_template_vars(message_template.template)
        for i, var_widget in enumerate(self.var_widgets):
            if i < len(var_indices):
                var_widget.set_menu(None, *message_template.variables[i])
            else:
                var_widget.set_menu()
        message_text = self.get_message_text()
        self.message_label.configure(text=message_text)

    def on_message_var_selected(self, selected_var):
        message_text = self.get_message_text()
        self.message_label.configure(text=message_text)

    def on_free_text_updated(self, message_text):
        self.logger.info(f"on_free_text_updated {message_text}")
        self.message_label.configure(text=message_text)
        return True

class MessageTemplate:
    def __init__(self, template, *args):
        self.template = template
        self.variables = args

class Accumulator:
    def __init__(self, initial=0):
        self.val = initial

    def get_next(self):
        self.val += 1
        return self.val - 1

def get_guides(test_guides=None):
    with open(os.path.join(os.path.dirname(__file__), "guides.csv"), encoding="utf-8") as f:
        guides = []
        for i, row in enumerate(csv.reader(f)):
            if i < 3:
                continue  # skip header lines
            if not row[0]:
                break
            guides.append(Guide(row[0], row[2]))
        guides.sort(key=lambda guide: guide.name)
    if test_guides:
        for guide in test_guides.split(","):
            name, number = guide.split(":")
            guides.append(Guide(name, number))
    return guides

def main():
    message_sender = MessageSender()
    message_sender.mainloop()

if __name__ == "__main__":
    main()
