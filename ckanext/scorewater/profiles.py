import json
from ckantoolkit import config
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, XSD, SKOS
from geomet import wkt, InvalidGeoJSONException
from ckan.plugins import toolkit
from ckanext.dcat.utils import resource_uri, publisher_uri_organization_fallback, DCAT_EXPOSE_SUBCATALOGS, DCAT_CLEAN_TAGS
from ckanext.dcat.profiles import RDFProfile, URIRefOrLiteral, CleanedURIRef
import logging
log = logging.getLogger(__name__)

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace('http://schema.org/')
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
DCATAP = Namespace('http://data.europa.eu/r5r/')
PROV = Namespace('http://www.w3.org/ns/prov#')
GEOJSON_IMT = 'https://www.iana.org/assignments/media-types/application/vnd.geo+json'

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'dcatap': DCATAP,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'prov': PROV,
}

PREFIX_TEL = u'tel:'

class DcatApSeTwoZeroZero(RDFProfile):
    '''
    A DCAT-AP-SE v2.0.0 RDF profile that validates under:

    https://registrera.oppnadata.se/toolkit/validate

    '''

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        # log.info(DCT['description'])
        # log.info(DCT['landingPage'])
        # try:
        #     log.info('get from schema')
        #     exampleDCT = namespaces.get('dct')
        #     log.info('success')
        #     result = exampleDCT['title']
        #     log.info(result)
        # except:
        #     log.info('failed')
        #     pass
        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # Basic fields
        items = [
            ('title', DCT.title, None, Literal),
            ('notes', DCT.description, None, Literal),
            ('url', DCAT.landingPage, None, URIRef),
            ('creator', DCT.creator, None, URIRef),
            ('attribution', PROV.qualifiedAttribution, None, Literal),
            ('identifier', DCT.identifier, ['guid', 'id'], Literal),
            ('alternate_id', ADMS.identifier, None, Literal),
            ('conforms_to', DCT.conformsTo, None, URIRef),
            ('temporal_resolution', DCAT.temporalResolution, None, Literal),
            ('spatial_resolution', DCAT.spatialResolutionInMeters, None, Literal),
            ('frequency', DCT.accrualPeriodicity, None, URIRef),
            ('version', ADMS.versionNotes, ['dcat_version'], Literal),
            ('version_notes', ADMS.versionNotes, None, Literal),
            ('source', DCT.source, None, URIRef),
            ('access_rights', DCT.accessRights, None, URIRef),
            ('fee', SCHEMA.offers, None, URIRef),
            ('has_version', DCT.hasVersion, None, URIRef),
            ('is_version_of', DCT.isVersionOf, None, URIRef),
            ('is_referenced_by', DCT.isReferencedBy, None, URIRef),
            ('relation', DCT.relation, None, URIRef),
            ('qualified_relation', DCAT.qualifiedRelation, None, URIRef),
            ('documentation', FOAF.page, None, Literal),
            ('provenance', DCT.provenance, None, Literal),
            ('distribution', DCAT.distribution, None, URIRef)
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        # Tags
        for tag in dataset_dict.get('tags', []):
            self.g.add((dataset_ref, DCAT.keyword, Literal(tag['name'])))

        # Dates
        items = [
            ('issued', DCT.issued, ['metadata_created'], Literal),
            ('modified', DCT.modified, ['metadata_modified'], Literal),
        ]
        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        #  Lists
        items = [
            ('language', DCT.language, None, URIRef),
            ('theme', DCAT.theme, None, URIRef),
        ]
        self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

        # Contact details
        if any([
            self._get_dataset_value(dataset_dict, 'contact_point_uri'),
            self._get_dataset_value(dataset_dict, 'contact_point_name'),
            self._get_dataset_value(dataset_dict, 'contact_point_email'),
            self._get_dataset_value(dataset_dict, 'contact_point_type'),
            self._get_dataset_value(dataset_dict, 'contact_point_phone'),
            self._get_dataset_value(dataset_dict, 'contact_point_address')
        ]):

            contact_uri = self._get_dataset_value(dataset_dict, 'contact_point_uri')
            contact_point_type = self._get_dataset_value(dataset_dict, 'contact_point_type')
            if contact_uri:
                contact_details = CleanedURIRef(contact_uri)
            else:
                contact_details = BNode()
            contact_point_type_ref = VCARD.Organization
            contact_point_ref = DCAT.contactPoint
            if contact_point_type:
                if contact_point_type == "individual":
                    contact_point_type_ref = VCARD.Individual

            g.add((contact_details, RDF.type, contact_point_type_ref))
            g.add((dataset_ref, contact_point_ref, contact_details))

            self._add_triple_from_dict(
                dataset_dict, contact_details,
                VCARD.fn, 'contact_point_name', None
            )
            # Add mail address as URIRef, and ensure it has a mailto: prefix
            self._add_triple_from_dict(
                dataset_dict, contact_details,
                VCARD.hasEmail, 'contact_point_email', None,
                _type=URIRef, value_modifier=self._add_mailto
            )
            # Add telephone as Literal, and ensure it has a tel: prefix
            telephone_ref = BNode()
            telephone = self._get_dataset_value(dataset_dict, 'contact_point_phone')
            self.g.add((contact_details, VCARD.hasTelephone, telephone_ref))
            self.g.add((telephone_ref, VCARD.hasValue, URIRef(self._add_tel(telephone))))

            # Assign address only to Locality property
            # has_address_ref = BNode()
            # address_ref = BNode()
            # address = self._get_dataset_value(dataset_dict, 'contact_point_address')
            # self.g.add((contact_details, VCARD.hasAddress, has_address_ref))
            # self.g.add((has_address_ref, VCARD.Address, address_ref))
            # self.g.add((address_ref, VCARD.Locality, Literal(address)))

        # Publisher
        if any([
            self._get_dataset_value(dataset_dict, 'publisher_uri'),
            self._get_dataset_value(dataset_dict, 'publisher_name'),
            dataset_dict.get('organization'),
        ]):

            publisher_uri = self._get_dataset_value(dataset_dict, 'publisher_uri')
            publisher_uri_fallback = publisher_uri_organization_fallback(dataset_dict)
            publisher_name = self._get_dataset_value(dataset_dict, 'publisher_name')
            if publisher_uri:
                publisher_details = CleanedURIRef(publisher_uri)
            elif not publisher_name and publisher_uri_fallback:
                # neither URI nor name are available, use organization as fallback
                publisher_details = CleanedURIRef(publisher_uri_fallback)
            else:
                # No publisher_uri
                publisher_details = BNode()

            g.add((publisher_details, RDF.type, FOAF.Organization))
            g.add((dataset_ref, DCT.publisher, publisher_details))

            # In case no name and URI are available, again fall back to organization.
            # If no name but an URI is available, the name literal remains empty to
            # avoid mixing organization and dataset values.
            if not publisher_name and not publisher_uri and dataset_dict.get('organization'):
                publisher_name = dataset_dict['organization']['title']

            g.add((publisher_details, FOAF.name, Literal(publisher_name)))
            # TODO: It would make sense to fallback these to organization
            # fields but they are not in the default schema and the
            # `organization` object in the dataset_dict does not include
            # custom fields
            items = [
                ('publisher_email', FOAF.mbox, None, URIRef),
                ('publisher_url', FOAF.homepage, None, URIRef),
                ('publisher_type', DCT.type, None, URIRefOrLiteral),
            ]

            self._add_triples_from_dict(dataset_dict, publisher_details, items)

        # Temporal
        start = self._get_dataset_value(dataset_dict, 'temporal_start')
        end = self._get_dataset_value(dataset_dict, 'temporal_end')
        if start or end:
            temporal_extent = BNode()
            g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
            if start:
                self._add_date_triple(temporal_extent, DCAT.startDate, start)
            if end:
                self._add_date_triple(temporal_extent, DCAT.endDate, end)
            g.add((dataset_ref, DCT.temporal, temporal_extent))

        # Spatial
        spatial_uri = self._get_dataset_value(dataset_dict, 'spatial_scheme')
        spatial_text = self._get_dataset_value(dataset_dict, 'spatial_text')
        spatial_geom = self._get_dataset_value(dataset_dict, 'spatial')

        if spatial_uri or spatial_text or spatial_geom:
            if spatial_uri:
                spatial_ref = CleanedURIRef(spatial_uri)
            else:
                spatial_ref = BNode()

            g.add((spatial_ref, RDF.type, DCT.Location))
            g.add((dataset_ref, DCT.spatial, spatial_ref))

            if spatial_text:
                g.add((spatial_ref, SKOS.prefLabel, Literal(spatial_text)))

            if spatial_geom:
                # GeoJSON
                g.add((spatial_ref,
                       LOCN.geometry,
                       Literal(spatial_geom, datatype=GEOJSON_IMT)))
                # WKT, because GeoDCAT-AP says so
                try:
                    g.add((spatial_ref,
                           LOCN.geometry,
                           Literal(wkt.dumps(json.loads(spatial_geom),
                                             decimals=4),
                                   datatype=GSP.wktLiteral)))
                except (TypeError, ValueError, InvalidGeoJSONException):
                    pass

        # Resources
        for resource_dict in dataset_dict.get('resources', []):

            distribution = URIRef(resource_uri(resource_dict))

            g.add((dataset_ref, DCAT.distribution, distribution))

            g.add((distribution, RDF.type, DCAT.Distribution))

            #  Simple values
            items = [
                ('name', DCT.title, None, Literal),
                ('description', DCT.description, None, Literal),
                ('status', ADMS.status, None, URIRef),
                ('license', DCT.license, None, Literal),
                ('availability', DCATAP.availability, None, URIRef),
            ]

            self._add_triples_from_dict(resource_dict, distribution, items)

            # Rights
            rights_ref = BNode()
            g.add((distribution, DCT.RightsStatement, rights_ref))
            g.add((rights_ref, DCT.rights, URIRefOrLiteral(resource_dict['rights'])))

            #  Lists
            items = [
                ('documentation', FOAF.page, None, URIRef),
                ('language', DCT.language, None, URIRef),
                ('conforms_to', DCT.conformsTo, None, Literal),
            ]
            self._add_list_triples_from_dict(resource_dict, distribution, items)

            # Format
            mimetype = resource_dict.get('mimetype')
            fmt = resource_dict.get('format')

            # IANA media types (either URI or Literal) should be mapped as mediaType.
            # In case format is available and mimetype is not set or identical to format,
            # check which type is appropriate.
            if fmt and (not mimetype or mimetype == fmt):
                if ('iana.org/assignments/media-types' in fmt
                        or not fmt.startswith('http') and '/' in fmt):
                    # output format value as dcat:mediaType instead of dct:format
                    mimetype = fmt
                    fmt = None
                else:
                    # Use dct:format
                    mimetype = None

            if mimetype:
                g.add((distribution, DCAT.mediaType,
                       URIRefOrLiteral(mimetype)))

            if fmt:
                g.add((distribution, DCT['format'],
                       URIRefOrLiteral(fmt)))

            # URL
            url = resource_dict.get('url')
            # TODO accessURL should always link to the CKAN /dataset/.../resource/...
            # get('url) for external resource won't return the acceptable value.
            g.add((distribution, DCAT.accessURL, URIRef(url)))
            g.add((distribution, DCAT.downloadURL, URIRef(url)))

            # Dates
            items = [
                ('issued', DCT.issued, None, Literal),
                ('modified', DCT.modified, None, Literal),
            ]

            self._add_date_triples_from_dict(resource_dict, distribution, items)

            # Numbers
            if resource_dict.get('size'):
                try:
                    g.add((distribution, DCAT.byteSize,
                           Literal(float(resource_dict['size']),
                                   datatype=XSD.decimal)))
                except (ValueError, TypeError):
                    g.add((distribution, DCAT.byteSize,
                           Literal(resource_dict['size'])))
            # Checksum
            if resource_dict.get('hash'):
                checksum = BNode()
                g.add((checksum, SPDX.checksumValue,
                       Literal(resource_dict['hash'],
                               datatype=XSD.hexBinary)))

                if resource_dict.get('hash_algorithm'):
                    if resource_dict['hash_algorithm'].startswith('http'):
                        g.add((checksum, SPDX.algorithm,
                               URIRef(resource_dict['hash_algorithm'])))
                    else:
                        g.add((checksum, SPDX.algorithm,
                               Literal(resource_dict['hash_algorithm'])))
                g.add((distribution, SPDX.checksum, checksum))

    def graph_from_catalog(self, catalog_dict, catalog_ref):

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((catalog_ref, RDF.type, DCAT.Catalog))

        # Basic fields
        items = [
            ('title', DCT.title, self.get_catalog_title(), Literal),
            ('description', DCT.description, self.get_catalog_description(), Literal),
            ('homepage', FOAF.homepage, config.get('ckan.site_url'), URIRef),
            ('themeTaxonomy', DCAT.themeTaxonomy, "http://publications.europa.eu/resource/authority/data-theme", URIRef),
            ('license', DCT.license, "http://creativecommons.org/publicdomain/zero/1.0/", URIRef),
            ('language', DCT.language, self.get_catalog_language(), URIRef),
            ('publisher', DCT.publisher, config.get('ckan.site_url', 'https://www.dataplattform.se/'), URIRef),
        ]
        for item in items:
            key, predicate, fallback, _type = item

            if catalog_dict:
                if key == 'language':
                    if fallback == 'd':
                        value = "http://publications.europa.eu/resource/authority/language/ENG"
                else:
                    value = catalog_dict.get(key, fallback)
            else:
                value = fallback
            if value:
                g.add((catalog_ref, predicate, _type(value)))

        # Dates
        issued = self._first_catalog_creation()
        if issued:
            self._add_date_triple(catalog_ref, DCT.issued, issued)

        modified = self._last_catalog_modification()
        if modified:
            self._add_date_triple(catalog_ref, DCT.modified, modified)

    def _first_catalog_creation(self):
        '''
        Returns the date and time an package on the catalog was first created

        To be more precise, the oldest value for `metadata_created` on a
        dataset.

        Returns a dateTime string in ISO format, or None if it could not be
        found.
        '''
        context = {
            'ignore_auth': True
        }
        result = toolkit.get_action('package_search')(context, {
            'sort': 'metadata_created asc',
            'rows': 1,
        })
        if result and result.get('results'):
            return result['results'][0]['metadata_modified']
        return None

    def _add_tel(self, telephone):
        '''
        Ensures that the mail address has an URIRef-compatible mailto: prefix.
        Can be used as modifier function for `_add_triple_from_dict`.
        '''
        if telephone:
            return PREFIX_TEL + self._without_mailto(telephone)
        else:
            return telephone

    def _without_tel(self, telephone):
        '''
        Ensures that the mail address string has no mailto: prefix.
        '''
        if telephone:
            return str(telephone).replace(PREFIX_TEL, u'')
        else:
            return telephone

    def get_catalog_title(self):
        default_catalog_title = 'Oppnadata DCAT catalog'
        get_catalog_title = config.get('ckan.site_title')
        return get_catalog_title if get_catalog_title != '' else default_catalog_title

    def get_catalog_description(self):
        default_catalog_description = 'No description provided'
        get_catalog_description = config.get('ckan.site_description')
        return get_catalog_description if get_catalog_description != '' else default_catalog_description

    def get_catalog_language(self):
        locale_default = config.get('ckan.locale_default', None)
        locale_dict = {'en': 'ENG', 'nl': 'NLD', 'sv': 'SWE'}
        language = 'http://publications.europa.eu/resource/authority/language/ENG'
        if locale_default:
            language = 'http://publications.europa.eu/resource/authority/language/{}'.format(locale_dict[locale_default])
        return language
