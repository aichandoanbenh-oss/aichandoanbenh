# Chicken body model – source and license

The chicken body classifier derives from the Evet-Africa poultry-disease-dataset
(https://huggingface.co/datasets/Evet-Africa/poultry-disease-dataset), published under
AGPL-3.0. The derived model and corresponding training component are provided under
AGPL-3.0; the full text is in licenses/chicken_body/AGPL-3.0.txt.

Corresponding source is included under scripts/, web/model_factory.py and
training_sources/. Initial model training: collect_chicken_body.py,
collect_chicken_body_controls.py, train_chicken_body.py,
prepare_chicken_improvement.py, train_available.py and prepare_cattle.py.
The current adaptation uses collect_round3_training.py, audit_round3_training.py,
prepare_round3_training.py and train_round3.py. Metadata, split manifests and
selection records are included; local raw-image paths must be reconstructed from
the cited sources, subject to each source's terms. Model files are not proprietary.

Additional sources include PoultryDVM and Ivan Dinev/The Poultry Site and Wikimedia
controls. Copyrights remain with their respective authors. Source photographs are
not included in this web repository. No unrestricted right to redistribute source
photographs is asserted. Labels are visible sign groups, not confirmed pathogens.
