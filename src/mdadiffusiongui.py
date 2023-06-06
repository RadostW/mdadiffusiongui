import yaml
import highlighter
import mdadiffusion
import logging
import numpy as np

import sys, os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QInputDialog,
    QLineEdit,
    QFileDialog,
    QMenu,
    QMenuBar,
    QGridLayout,
    QPlainTextEdit,
    QShortcut,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtGui import QIcon, QKeySequence
from qt_material import apply_stylesheet


def numpy_to_arrays(d):
    def denumpy(x):
        if isinstance(x, np.ndarray) or isinstance(x, np.float_):
            return x.tolist()
        elif isinstance(x, dict):
            return denumpy(x)
        else:
            return x

    return {denumpy(k): denumpy(v) for k, v in d.items()}


def round_floats(d):
    def rf(x):
        if isinstance(x, float):
            return round(x, 4)
        elif isinstance(x, dict):
            return round_floats(x)
        else:
            return x

    return {k: rf(v) for k, v in d.items()}


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "Diffusion with Minimum Dissipation Approximation."
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

        self.computation_result = dict()
        self.global_config = dict()
        self.protein_config = dict()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QGridLayout()
        self.setLayout(layout)

        menubar = QMenuBar()
        layout.addWidget(menubar, 0, 0, 1, 3)

        # ----- fileMenu -----
        fileMenu = menubar.addMenu("File")
        configAction = fileMenu.addAction("Load config")
        proteinAction = fileMenu.addAction("Load protein")

        fileMenu.addSeparator()  # ----
        saveAction = fileMenu.addAction("Save results")
        fileMenu.addSeparator()  # ----
        quitAction = fileMenu.addAction("Quit")

        quitShortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quitAction.triggered.connect(self.handleCloseAction)
        quitShortcut.activated.connect(self.handleCloseAction)

        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveAction.triggered.connect(self.handleSaveAction)
        saveShortcut.activated.connect(self.handleSaveAction)

        configShortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        configAction.triggered.connect(self.handleConfigAction)
        configShortcut.activated.connect(self.handleConfigAction)

        proteinShortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        proteinAction.triggered.connect(self.handleProteinAction)
        proteinShortcut.activated.connect(self.handleProteinAction)

        runShortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        runShortcut.activated.connect(self.handleRunAction)

        # ----- help menu -----
        help_menu = menubar.addMenu("Help")  # TODO
        helpConfigAction = help_menu.addAction("Config help")  # TODO
        helpKeyboardAction = help_menu.addAction("Keyboard shortcuts")
        helpKeyboardAction.triggered.connect(self.handleKeyboardHelp)
        help_menu.addSeparator()  # ----
        helpKeyboardAction = help_menu.addAction("How to cite")  # TODO

        # add textbox
        tbox = QPlainTextEdit()
        layout.addWidget(QLabel("Global configuration"), 1, 0)
        layout.addWidget(QLabel("Protein configuration"), 1, 1)
        layout.addWidget(QLabel("Results"), 1, 2)

        self.global_config_panel = QPlainTextEdit()
        self.global_config_panel.setReadOnly(True)
        self.protein_config_panel = QPlainTextEdit()
        self.protein_config_panel.setReadOnly(True)

        self.results_panel = QPlainTextEdit()
        self.results_panel.setReadOnly(True)

        self.highlight_global = highlighter.SimpleYamlHighlighter(
            self.global_config_panel.document()
        )
        self.highlight_protein = highlighter.SimpleYamlHighlighter(
            self.protein_config_panel.document()
        )

        self.highlight_results = highlighter.SimpleYamlHighlighter(
            self.results_panel.document()
        )

        layout.addWidget(self.global_config_panel, 2, 0)
        layout.addWidget(self.protein_config_panel, 2, 1)
        layout.addWidget(self.results_panel, 2, 2)

        self.compute_button = QPushButton("Compute")
        layout.addWidget(self.compute_button, 3, 0, 1, 3)
        self.compute_button.clicked.connect(self.handleRunAction)

        self.show()

    def handleCloseAction(self):
        self.close()

    def handleSaveAction(self):
        filename = self.saveFileDialog()
        if self.computation_result != None:
            with open(filename, "w") as out_file:
                out_file.write(
                    yaml.dump(round_floats(numpy_to_arrays(self.computation_result)))
                )

    def handleProteinAction(self):
        filename = self.openFileNameDialog(title="Load annotated sequence")
        if filename:
            with open(filename) as in_file:
                self.protein_config = yaml.safe_load(in_file)
                print(self.protein_config)
                self.protein_config_panel.setPlainText(yaml.dump(self.protein_config))

    def handleConfigAction(self):
        filename = self.openFileNameDialog(title="Load global config")
        if filename:
            with open(filename) as in_file:
                self.global_config = yaml.safe_load(in_file)
                print(self.global_config)
                self.global_config_panel.setPlainText(yaml.dump(self.global_config))

    def handleKeyboardHelp(self):
        self.popup = QMessageBox()
        self.popup.setText(
            """
            Keyboard shortcuts:
            [Ctrl+E] -- load config
            [Ctrl+O] -- load protein            
            [Ctrl+R] -- run
            [Ctrl+S] -- save results
            [Ctrl+Q] -- quit
            """
        )
        self.popup.exec()

    def handleRunAction(self):
        try:
            bead_model = mdadiffusion.mda.bead_model_from_sequence(
                annotated_sequence=self.protein_config["AnnotatedSequence"],
                effective_density=self.global_config["OrderedBeads"][
                    "EffectiveDensity"
                ],
                hydration_thickness=self.global_config["OrderedBeads"][
                    "HydrationThickness"
                ],
                disordered_radii=self.global_config["DisorderedBeads"][
                    "HydrodynamicRadius"
                ],
                c_alpha_distance=self.global_config["DisorderedBeads"][
                    "CAlphaDistance"
                ],
                aa_masses=self.global_config["AminoAcidMasses"],
            )

            rh_dict = mdadiffusion.mda.hydrodynamic_size(
                bead_steric_radii=bead_model["steric_radii"],
                bead_hydrodynamic_radii=bead_model["hydrodynamic_radii"],
                ensemble_size=100,
                bootstrap_rounds=20,
            )

            self.computation_result['HydrodynamicRadius_MDA'] = rh_dict['rh_mda']
            self.computation_result['HydrodynamicRadius_MDA_error'] = rh_dict['rh_mda (se)']
            self.computation_result['HydrodynamicRadius_Kirkwood'] = rh_dict['rh_kr']
            self.computation_result['HydrodynamicRadius_Kirkwood_error'] = rh_dict['rh_kr (se)']

            self.computation_result['ProteinName'] = self.protein_config["ProteinName"]
            self.computation_result['AnnotatedSequence'] = self.protein_config["AnnotatedSequence"]

            self.results_panel.setPlainText(
                yaml.dump(round_floats(numpy_to_arrays(self.computation_result)))
            )

        except Exception as e:
            self.popup = QMessageBox()
            self.popup.setText(logging.traceback.format_exc())
            self.popup.exec()
            self.handleCloseAction()

    def openFileNameDialog(self, title=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, title, "", "All Files (*);;Yaml Files (*.yaml)", options=options
        )
        if fileName:
            print(fileName)
        return fileName

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save computation results",
            "",
            "All Files (*);;Yaml Files (*.yaml)",
            options=options,
        )
        if fileName:
            print(fileName)
        return fileName


if __name__ == "__main__":
    app = QApplication(sys.argv)

    apply_stylesheet(app, theme="dark_amber.xml")

    stylesheet = app.styleSheet()

    with open("css/custom.css") as css_file:
        app.setStyleSheet(stylesheet + css_file.read().format(**os.environ))

    ex = App()
    sys.exit(app.exec_())
