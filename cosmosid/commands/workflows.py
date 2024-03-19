from cliff.lister import Lister
from cosmosid.enums import WF_DESCRIPTION, SAMPLE_TYPES, WF_NAME_TO_CLI_NAME, HIDDEN_WFS
from cosmosid.helpers.exceptions import CosmosidConnectionError, CosmosidServerError, AuthenticationFailed


class Workflows(Lister):
    """Show enabled workflows."""

    @staticmethod
    def prerare_wfs_output(wfs):
        res = []
        for wf in wfs:
            if wf['name'] in HIDDEN_WFS:
                continue
            
            all_meta = {
                meta_item['meta_type']: meta_item['properties']
                for meta_item in wf['metadata']
            }
            
            if all_meta.get('workflow', {}).get('type') not in (None, 'batch'):
                continue
            
            sample_types = ','.join(
                filter(
                    lambda str_type: str_type is not None,
                    [SAMPLE_TYPES.get(str(type_)) for type_ in all_meta.get('input_param', {}).get('sample_types', [])], 
            ))
            
            if not sample_types:
                continue
                    
            res.append(
                (WF_NAME_TO_CLI_NAME.get(wf['name'], wf['name']), wf['version'], str(sample_types), WF_DESCRIPTION.get((wf['name'], wf['version'])))
            )
        return sorted(res, key=lambda item: f'{item[0].lower()}{item[1]}')
        

    def take_action(self, parsed_args):
        """get json with items and prepare for output"""
        
        try:
            enabled_workflows = self.app.cosmosid.get_enabled_workflows()
        except CosmosidServerError:
            self.app.logger.error("Server error occurred while getting workflows")
        except AuthenticationFailed:
            self.app.logger.error("Authentication failed, make sure you have valid api-key")
        except CosmosidConnectionError:
            self.app.logger.error("Connection error occurred while getting workflows")
        return (
            ('Name', 'Version', 'Sample Type', 'Description'),
            self.prerare_wfs_output(enabled_workflows)
        )
