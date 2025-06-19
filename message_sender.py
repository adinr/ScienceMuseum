import tkinter
import tkinter.ttk
import pywhatkit
import csv


class Guide:
	def __init__(self, name, number):
		self.name = name
		self.number = f"+972{number[1:].replace("-", "")}"
		print(self.number)
		self.var = tkinter.IntVar(value=0)

class MessageSender:
	def __init__(self, message_widget, message_widget_var, guides, message_templates_dict, var_widgets, template_vars, message_label):
		self.message_widget = message_widget
		self.message_widget_var = message_widget_var
		self.guides = guides
		self.message_templates_dict = message_templates_dict
		self.var_widgets = var_widgets
		self.template_vars = template_vars
		self.message_label = message_label

class MessageTemplate:
	def __init__(self, template, *args):
		self.template = template
		self.variables = args

def get_message_text():
	message_text = message_sender.message_widget_var.get()
	message_text = message_text.format(*[template_var.get() for template_var in message_sender.template_vars[:len(find_template_vars(message_text))]])
	message_sender.message_label.configure(text=message_text)
	return message_text

def send_message():
	message_text = get_message_text()
	if not message_text:
		print("no message")
		return
	print(f"sending message {message_text} to")
	for guide in message_sender.guides:
		if guide.var.get():
			print(guide.number)
			pywhatkit.sendwhatmsg_instantly(guide.number, message_text, wait_time=20, tab_close=True)

def find_template_vars(template):
	i = template.find("{}")
	vars = []
	while i >= 0:
		vars.append(i)
		i = template.find("{}", i + 1)
	return vars

def on_message_template_seleccted(selected_message_template):
	print(f"on_message_template_seleccted {selected_message_template}")
	message_template = message_sender.message_templates_dict[selected_message_template]
	var_indices = find_template_vars(message_template.template)
	for i, var_widget in enumerate(message_sender.var_widgets):
		if i < len(var_indices):
			var_widget.set_menu(None, *message_template.variables[i])
		else:
			var_widget.set_menu()
	message_text = get_message_text()
	message_sender.message_label.configure(text=message_text)

def on_message_var_selected(selected_var):
	message_text = get_message_text()
	message_sender.message_label.configure(text=message_text)

def get_guides():
	with open("guides.csv", encoding="utf-8") as f:
		guides = []
		for i, row in enumerate(csv.reader(f)):
			if i < 3:
				continue  # skip header lines
			if not row[0]:
				break
			guides.append(Guide(row[0], row[2]))
	return guides

def message_sender_form():
	global message_sender
	root = tkinter.Tk()
	frm = tkinter.ttk.Frame(root, padding=10)
	frm.grid()
	tkinter.ttk.Label(frm, text="מי פנוי באלנבי?").grid(column=0, row=0)
	tkinter.ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
	guides = get_guides()
	receipt_check_boxes = []
	for i, guide in enumerate(guides):
		check_button = tkinter.ttk.Checkbutton(frm, text=guide.name, variable=guide.var)
		check_button.grid(column=i % 2, row=i // 2 + 1)
		receipt_check_boxes.append(check_button)
	sessions = ["ראשון", "שני", "שלישי", "רביעי"]
	days = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
	message_templates = [
		MessageTemplate("היי, אפשרי לך לקחת מחזור {} ביום {}?", sessions, days),
		MessageTemplate("היי, הקבוצה של מחזור {} ביום {} ביטלה.", sessions, days),
		MessageTemplate("היי, הקבוצה של מחזור {} ביום {} {} ב{}. אפשרי לך?", sessions, days, ["מאחרת", "מקדימה"], ["15 דקות", "30 דקות", "שעה"]),
		MessageTemplate("תודה!")
	]
	message_templates_dict = {template.template: template for template in message_templates}
	message_widget_var = tkinter.StringVar()
	message_widget = tkinter.ttk.OptionMenu(frm, message_widget_var, None, *[template.template for template in message_templates], command=on_message_template_seleccted)
	template_vars = []
	var_widgets = []
	for i in range(4):
		message_template_var = tkinter.StringVar()
		var_widget = tkinter.ttk.OptionMenu(frm, message_template_var, command=on_message_var_selected)
		var_widget.grid(column=0, row=len(guides) // 2 + i + 2)
		var_widgets.append(var_widget)
		template_vars.append(message_template_var)
	message_widget.grid(column=0, row=len(guides) // 2 + 1)
	message_label = tkinter.ttk.Label(frm)
	message_label.grid(column = 0, row=len(guides) // 2 + 6)
	tkinter.ttk.Button(frm, text="Send", command=send_message).grid(column=1, row=len(guides) // 2 + 6)
	message_sender = MessageSender(message_widget, message_widget_var, guides, message_templates_dict, var_widgets, template_vars, message_label)
	root.mainloop()


if __name__ == "__main__":
	message_sender_form()
