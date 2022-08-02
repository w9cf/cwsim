.PHONY: pyqt6 pyqt5 cwsim.exe

cwsimgui.py: cwsimgui.ui
	pyuic6 -i 3 -o cwsimgui.py cwsimgui.ui

pyqt5:
	pyuic5 -i 3 -o cwsimgui.py cwsimgui.ui

pyqt6:
	pyuic6 -i 3 -o cwsimgui.py cwsimgui.ui

cwsim.exe: pyqt6
	pyinstaller.exe -w -F --clean --add-data "MASTER.SCP;." --add-data "cwsimgui.ui;." -n cwsim cwsim.py

distclean:
	rm -rf cwsimgui.py
	rm -rf __pycache__
	rm -f *.pyc
