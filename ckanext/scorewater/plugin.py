import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import validators as v


class ScorewaterPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IValidator
    def get_validators(self):
        return {
            'url_checker': v.url_checker
        }
