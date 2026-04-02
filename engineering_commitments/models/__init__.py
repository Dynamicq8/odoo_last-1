# engineering_commitments/models/__init__.py
# -*- coding: utf-8 -*-
from . import sign_template
from . import project_project # This needs to be imported for ProjectProject model and its company_contract_ids field
from . import project_task
from . import engineering_task_commitment
from . import engineering_project_commitment
# You had 'engineering_project_contract' twice, which likely doesn't exist.
# Assuming 'engineering.project.company.contract' is defined in 'project_project.py' (as per my combined code)
# and 'engineering.task.company.contract' is defined in 'project_task.py' (as per my combined code),
# then importing 'project_project' and 'project_task' is sufficient.