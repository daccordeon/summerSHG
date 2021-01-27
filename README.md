# summerSHG
## README.md
*Originally was planned to be a characterisation of the new second-harmonic generator (SHG), however, instead is a characterisation of the tilt lock (TL) control system for the OPO cavity length.*

James Gardner, January 2021

Current build found [here](https://github.com/daccordeon/summerSHG).

Note that the netgpibdata folder's contents are not my work, please find the source code [here](https://github.com/awade/netgpibdata).

---
Guide to replicating results:

- Download the repo and check that your system satisfies the requirements below.
- Download the data files available in the release [here](https://github.com/daccordeon/summerSHG/releases/tag/v1.0).
- Extract all data files into the data folder such that the source code in the source folder can reach them as "../data/". Alternatively, set a different PATH_TO_DATA constant in the source code.
- Open up jupyter-notebook and run, in their entirety, TL_plotting_and_manual_stitching.ipynb and TL_open_and_closed_loop_gain.ipynb. They are not dependent on each other and can be run separately.
- This should produce all of the processed Python 3 plots used in the technical notes. Some other figures can be found in the report/figures folder and uploaded to the CGP Logbook. Note that the LaTeX files will error out without all figures present, comment the includegraphics commands out to see the text of the report.
- Contact the authors for any technical enquiries at <u6069809@anu.edu.au>.

Requirements:
- ipython==5.5.0
- jupyter==1.0.0
- jupyter-client==5.2.2
- jupyter-console==6.0.0
- jupyter-core==4.4.0
- matplotlib==3.0.3
- numpy==1.16.2
- scipy==1.2.1
- netgpibdata as of [this commit](https://github.com/awade/netgpibdata/commit/3974fbadcb1a6dac8e644334917a060e910ccee3).

---
file structure
```bash
.
├── .gitignore
├── README.md
├── LICENSE
├── data
│   ├── README.md
│   └── (extract data files to here)
├── netgpibdata
│   ├── README.md
│   ├── SRmeasure.py
│   ├── README_basic_command.md
│   └── ...
├── report
│   ├── figures
│   │   ├── README.txt
│   │   ├── (place figures here to include them in the reports)
│   │   └── ...
│   ├── README.md
│   ├── short_report_main.tex
│   ├── short_report.bib
│   ├── technical_notes_main.tex
│   ├── technical_notes.bib
│   └── myunsrt.bst
└── source
    ├── README.md
    ├── TL_open_and_closed_loop_gain.ipynb
    └── TL_plotting_and_manual_stitching.ipynb
```
[//]: # (tree -I '*.pdf|*.png')
