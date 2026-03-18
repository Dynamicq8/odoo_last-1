{
    'name': "Engineering Project Enhancements",
    'summary': "Links projects to sales orders and manages engineering project workflows.",
    'author': "Engineering Office",
    'category': 'Services/Engineering',
    'version': '17.0.1.0.0',
    'depends': [
        'project',
        'sale_management',
        'engineering_core',
        'sign', # It seems like you're using sign templates, so this dependency might be missing
    ],
    'data': [
        # === IMPORTANT: Define your model's Python files FIRST ===
        # Assuming your models (like EngineeringProjectCommitment) are defined here.
        # If project_task.py also defines models, it should be here.
        'views/project_project_views.xml', # If this file defines models too
        'data/project_task_type_data.xml', # If this file defines models too
        'data/cron.xml', # If this file defines models too

        # Example: if your models are in 'models/engineering_project_models.py'
        # 'models/engineering_project_models.xml', # Uncomment and adjust if you have a separate models XML
        
        # This is where your project_task.py is likely referenced (as it defines models).
        # You need to ensure the XML views that introduce the model also load it.
        # If your model `engineering.project.commitment` is defined in a Python file
        # but not referenced in an XML file for its view, you might need an empty XML file
        # or ensure its definition is loaded early.
        
        # If project_task.py contains the definition of EngineeringProjectCommitment:
        # You might need to add a data file that forces the loading of the model XML id
        # or ensure it's loaded as part of other view XMLs.
        
        # If your models are in a file like 'models/models.py', make sure it's loaded.
        # For new custom models, usually, their views are loaded before security.
        
        # === YOUR MODEL DEFINITION MUST BE LOADED BEFORE ACCESS RULES ===
        # The key is that model_engineering_project_commitment needs to exist BEFORE ir.model.access.csv is parsed.
        # Often, this means the XML files that define views for the model, or a dummy XML file to load the model,
        # need to come *before* security.
        
        # Let's try moving security down:
        'reports/initial_design_report.xml',
        'views/project_project_views.xml', # Assuming this view refers to the new model
        'data/project_task_type_data.xml',
        'data/cron.xml',
        
        # Place security AFTER all XMLs that define or reference models and their views.
        'security/ir.model.access.csv', # <--- MOVE THIS TO THE END OF THE 'data' LIST
    ],
    'assets': {
        'web.assets_backend': [
            'engineering_project/static/src/css/task_state.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
