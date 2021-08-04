# -*- coding:utf-8 -*-
from urllib.parse import urlparse
from urllib.parse import urlunparse

from datetime import datetime, timedelta

from flask import Blueprint, g
from flask import (
    render_template,
    redirect,
    abort,
    current_app,
    make_response,
    request,
    url_for,
    session
)

from atlas import utils
from atlas.configuration import config
from atlas.modeles.entities import vmTaxons, vmCommunes
from atlas.modeles.repositories import (
    vmTaxonsRepository,
    vmObservationsRepository,
    vmAltitudesRepository,
    vmMoisRepository,
    vmTaxrefRepository,
    vmCommunesRepository,
    vmObservationsMaillesRepository,
    vmMedias,
    vmCorTaxonAttribut,
    vmTaxonsMostView,
)

if current_app.config["EXTENDED_AREAS"]:
    from atlas.modeles.repositories import vmAreasRepository

# Adding functions for multilingual url process if MULTILINGUAL = True
if config.MULTILINGUAL:
    main = Blueprint("main", __name__, url_prefix='/<lang_code>')

    @main.url_defaults
    def add_language_code(endpoint, values):
        if 'language' not in session:
            session['language'] = config.BABEL_DEFAULT_LOCALE
        g.lang_code=session['language']
        values.setdefault('lang_code', g.lang_code )

    @main.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code')

else:
    main = Blueprint("main", __name__)

index_bp = Blueprint("index_bp", __name__)


@main.context_processor
def global_variables():
    db_session = utils.loadSession()
    values = {}

    if current_app.config["EXTENDED_AREAS"]:
        values["areas_type_search"] = vmAreasRepository.area_types(db_session)
    db_session.close()
    return values

@main.route(
    "/espece/" + current_app.config["REMOTE_MEDIAS_PATH"] + "<image>",
    methods=["GET", "POST"]
)
def especeMedias(image):
    return redirect(
        current_app.config["REMOTE_MEDIAS_URL"]
        + current_app.config["REMOTE_MEDIAS_PATH"]
        + image
    )


@main.route(
    "/commune/" + current_app.config["REMOTE_MEDIAS_PATH"] + "<image>",
    methods=["GET", "POST"],
)
def communeMedias(image):
    return redirect(
        current_app.config["REMOTE_MEDIAS_URL"]
        + current_app.config["REMOTE_MEDIAS_PATH"]
        + image
    )


@main.route(
    "/liste/" + current_app.config["REMOTE_MEDIAS_PATH"] + "<image>",
    methods=["GET", "POST"],
)
def listeMedias(image):
    return redirect(
        current_app.config["REMOTE_MEDIAS_URL"]
        + current_app.config["REMOTE_MEDIAS_PATH"]
        + image
    )


@main.route(
    "/groupe/" + current_app.config["REMOTE_MEDIAS_PATH"] + "<image>",
    methods=["GET", "POST"],
)
def groupeMedias(image):
    return redirect(
        current_app.config["REMOTE_MEDIAS_URL"]
        + current_app.config["REMOTE_MEDIAS_PATH"]
        + image
    )


@main.route(
    "/" + current_app.config["REMOTE_MEDIAS_PATH"] + "<image>", methods=["GET", "POST"]
)
def indexMedias(image):
    return redirect(
        current_app.config["REMOTE_MEDIAS_URL"]
        + current_app.config["REMOTE_MEDIAS_PATH"]
        + image
    )

@main.route("/", methods=["GET", "POST"])
@index_bp.route("/", methods=["GET", "POST"])
def index():
    session = utils.loadSession()
    connection = utils.engine.connect()
    if current_app.config["AFFICHAGE_DERNIERES_OBS"]:
        if current_app.config["AFFICHAGE_MAILLE"]:
            current_app.logger.debug("start AFFICHAGE_MAILLE")
            observations = vmObservationsMaillesRepository.lastObservationsMailles(
                connection,
                str(current_app.config["NB_DAY_LAST_OBS"]) + ' day',
                current_app.config["ATTR_MAIN_PHOTO"],
            )
            current_app.logger.debug("end AFFICHAGE_MAILLE")
        else:
            current_app.logger.debug("start AFFICHAGE_PRECIS")
            observations = vmObservationsRepository.lastObservations(
                connection,
                str(current_app.config["NB_DAY_LAST_OBS"]) + ' day',
                current_app.config["ATTR_MAIN_PHOTO"],
            )
            current_app.logger.debug("end AFFICHAGE_PRECIS")
    else:
        observations = []

    current_app.logger.debug("start mostViewTaxon")
    mostViewTaxon = vmTaxonsMostView.mostViewTaxon(connection)
    current_app.logger.debug("end mostViewTaxon")
    stat = vmObservationsRepository.statIndex(connection)
    current_app.logger.debug("start customStat")

    if current_app.config["AFFICHAGE_RANG_STAT"]:
        customStat = vmObservationsRepository.genericStat(
            connection, current_app.config["RANG_STAT"]
        )
        current_app.logger.debug("end customStat")
        current_app.logger.debug("start customStatMedia")
        customStatMedias = vmObservationsRepository.genericStatMedias(
            connection, current_app.config["RANG_STAT"]
        )
        current_app.logger.debug("end customStatMedia")
    else:
        customStat = []
        customStatMedias = []

    connection.close()
    session.close()

    print(observations)

    return render_template(
        "templates/home/_main.html",
        observations=observations,
        mostViewTaxon=mostViewTaxon,
        stat=stat,
        customStat=customStat,
        customStatMedias=customStatMedias,
    )


@main.route("/espece/<int:cd_ref>", methods=["GET", "POST"])
def ficheEspece(cd_ref):
    db_session = utils.loadSession()
    connection = utils.engine.connect()

    cd_ref = int(cd_ref)
    taxon = vmTaxrefRepository.searchEspece(connection, cd_ref)
    altitudes = vmAltitudesRepository.getAltitudesChilds(connection, cd_ref)
    months = vmMoisRepository.getMonthlyObservationsChilds(connection, cd_ref)
    synonyme = vmTaxrefRepository.getSynonymy(connection, cd_ref)
    communes = vmCommunesRepository.getCommunesObservationsChilds(connection, cd_ref)
    taxonomyHierarchy = vmTaxrefRepository.getAllTaxonomy(db_session, cd_ref)
    firstPhoto = vmMedias.getFirstPhoto(
        connection, cd_ref, current_app.config["ATTR_MAIN_PHOTO"]
    )
    photoCarousel = vmMedias.getPhotoCarousel(
        connection, cd_ref, current_app.config["ATTR_OTHER_PHOTO"]
    )
    videoAudio = vmMedias.getVideo_and_audio(
        connection,
        cd_ref,
        current_app.config["ATTR_AUDIO"],
        current_app.config["ATTR_VIDEO_HEBERGEE"],
        current_app.config["ATTR_YOUTUBE"],
        current_app.config["ATTR_DAILYMOTION"],
        current_app.config["ATTR_VIMEO"],
    )
    articles = vmMedias.getLinks_and_articles(
        connection,
        cd_ref,
        current_app.config["ATTR_LIEN"],
        current_app.config["ATTR_PDF"],
    )
    taxonDescription = vmCorTaxonAttribut.getAttributesTaxon(
        connection,
        cd_ref,
        current_app.config["ATTR_DESC"],
        current_app.config["ATTR_COMMENTAIRE"],
        current_app.config["ATTR_MILIEU"],
        current_app.config["ATTR_CHOROLOGIE"],
    )
    observers = vmObservationsRepository.getObservers(connection, cd_ref)

    connection.close()
    db_session.close()

    return render_template(
        "templates/specieSheet/_main.html",
        taxon=taxon,
        listeTaxonsSearch=[],
        observations=[],
        cd_ref=cd_ref,
        altitudes=altitudes,
        months=months,
        synonyme=synonyme,
        communes=communes,
        taxonomyHierarchy=taxonomyHierarchy,
        firstPhoto=firstPhoto,
        photoCarousel=photoCarousel,
        videoAudio=videoAudio,
        articles=articles,
        taxonDescription=taxonDescription,
        observers=observers,
    )


@main.route("/commune/<insee>", methods=["GET", "POST"])
def ficheCommune(insee):
    session = utils.loadSession()
    connection = utils.engine.connect()

    listTaxons = vmTaxonsRepository.getTaxonsCommunes(connection, insee)
    commune = vmCommunesRepository.getCommuneFromInsee(connection, insee)
    if current_app.config["AFFICHAGE_MAILLE"]:
        observations = vmObservationsMaillesRepository.lastObservationsCommuneMaille(
            connection, current_app.config["NB_LAST_OBS"], insee
        )
    else:
        observations = vmObservationsRepository.lastObservationsCommune(
            connection, current_app.config["NB_LAST_OBS"], insee
        )

    if current_app.config["EXTENDED_AREAS"]:
        id_area = vmAreasRepository.get_id_area(session, "COM", insee)
        surroundingAreas = vmAreasRepository.get_surrounding_areas(session, id_area)
    else:
        surroundingAreas = []

    observers = vmObservationsRepository.getObserversCommunes(connection, insee)

    session.close()
    connection.close()

    return render_template(
        "templates/areaSheet/_main.html",
        sheetType="commune",
        surroundingAreas=surroundingAreas,
        listTaxons=listTaxons,
        areaInfos=commune,
        observations=observations,
        observers=observers,
        DISPLAY_EYE_ON_LIST=True,
    )


@main.route("/liste/<cd_ref>", methods=["GET", "POST"])
def ficheRangTaxonomie(cd_ref):
    session = utils.loadSession()
    connection = utils.engine.connect()

    listTaxons = vmTaxonsRepository.getTaxonsChildsList(connection, cd_ref)
    referenciel = vmTaxrefRepository.getInfoFromCd_ref(session, cd_ref)
    taxonomyHierarchy = vmTaxrefRepository.getAllTaxonomy(session, cd_ref)
    observers = vmObservationsRepository.getObservers(connection, cd_ref)

    connection.close()
    session.close()

    return render_template(
        "templates/taxoRankSheet/_main.html",
        listTaxons=listTaxons,
        referenciel=referenciel,
        taxonomyHierarchy=taxonomyHierarchy,
        observers=observers,
        DISPLAY_EYE_ON_LIST=False,
    )


@main.route("/groupe/<groupe>", methods=["GET", "POST"])
def ficheGroupe(groupe):
    session = utils.loadSession()
    connection = utils.engine.connect()

    groups = vmTaxonsRepository.getAllINPNgroup(connection)
    listTaxons = vmTaxonsRepository.getTaxonsGroup(connection, groupe)
    observers = vmObservationsRepository.getGroupeObservers(connection, groupe)

    session.close()
    connection.close()

    return render_template(
        "templates/groupSheet/_main.html",
        listTaxons=listTaxons,
        referenciel=groupe,
        groups=groups,
        observers=observers,
        DISPLAY_EYE_ON_LIST=False,
    )


@main.route("/photos", methods=["GET", "POST"])
def photos():
    session = utils.loadSession()
    connection = utils.engine.connect()

    groups = vmTaxonsRepository.getINPNgroupPhotos(connection)

    session.close()
    connection.close()
    return render_template("templates/photoGalery/_main.html", groups=groups)


@main.route("/<page>", methods=["GET", "POST"])
def get_staticpages(page):
    session = utils.loadSession()
    if page not in current_app.config["STATIC_PAGES"]:
        abort(404)
    static_page = current_app.config["STATIC_PAGES"][page]
    session.close()
    return render_template(static_page["template"])


@main.route("/sitemap.xml", methods=["GET"])
def sitemap():
    """Generate sitemap.xml iterating over static and dynamic routes to make a list of urls and date modified"""
    pages = []
    ten_days_ago = datetime.now() - timedelta(days=10)
    session = utils.loadSession()
    connection = utils.engine.connect()
    url_root = request.url_root
    if url_root[-1] == "/":
        url_root = url_root[:-1]
    for rule in current_app.url_map.iter_rules():
        # check for a 'GET' request and that the length of arguments is = 0 and if you have an admin area that the rule does not start with '/admin'
        if (
            "GET" in rule.methods
            and len(rule.arguments) == 0
            and not rule.rule.startswith("/api")
        ):
            pages.append([url_root + rule.rule, ten_days_ago])

    # get dynamic routes for blog
    species = session.query(vmTaxons.VmTaxons).order_by(vmTaxons.VmTaxons.cd_ref).all()
    for specie in species:
        url = url_root + url_for("main.ficheEspece", cd_ref=specie.cd_ref)
        modified_time = ten_days_ago
        pages.append([url, modified_time])

    municipalities = (
        session.query(vmCommunes.VmCommunes).order_by(vmCommunes.VmCommunes.insee).all()
    )
    for municipalitie in municipalities:
        url = url_root + url_for("main.ficheCommune", insee=municipalitie.insee)
        modified_time = ten_days_ago
        pages.append([url, modified_time])

    sitemap_template = render_template(
        "templates/sitemap.xml",
        pages=pages,
        url_root=url_root,
        last_modified=ten_days_ago,
    )
    response = make_response(sitemap_template)
    response.headers["Content-Type"] = "application/xml"
    return response


@main.route("/robots.txt", methods=["GET"])
def robots():
    robots_template = render_template("templates/robots.txt")
    response = make_response(robots_template)
    response.headers["Content-type"] = "text/plain"
    return response

#Changing language
if config.MULTILINGUAL:
    @main.route('/language/<language>', methods=["GET", "POST"])
    def set_language(language=None):
        print('LANGUE : ' + language)
        session['language'] = language

        is_language_id = False
        actual_lang_id = config.BABEL_DEFAULT_LOCALE
        url_redirection = request.referrer
        url_parsed = urlparse(request.referrer)

        #Check if there is already a language in url
        for lang_id in config.LANGUAGES.keys():
            if url_parsed.path.find(('/') + lang_id +('/')) != -1:
                actual_lang_id = lang_id
                is_language_id=True
                break

        #If they're  language_id -> replacing it with new one
        if is_language_id:
            url_parsed = url_parsed._replace(path=url_parsed.path.replace('/' + actual_lang_id + '/', '/' + language + '/'))
            print('/' + actual_lang_id + '/')
            print('/' + language + '/')
            print(url_parsed)
        #If they're no language_id -> adding it to url
        else:
            #If there's not '/' at the end of index url
            if  url_parsed.path[len(url_parsed.path)-1] != '/' : 
                url_parsed = url_parsed._replace(path=url_parsed.path + '/' + language + '/')  
            #If there's '/' at the end of index url
            else:   
                url_parsed = url_parsed._replace(path=url_parsed.path + language + '/')   
        
        url_redirection = urlunparse(url_parsed)

        print(url_redirection)
        return redirect(url_redirection)

if current_app.config["EXTENDED_AREAS"]:

    @main.route("/area/<type_code>/<area_code>", methods=["GET", "POST"])
    def areaSheet(type_code, area_code):
        session = utils.loadSession()
        connection = utils.engine.connect()
        id_area = vmAreasRepository.get_id_area(session, type_code, area_code)
        listTaxons = vmAreasRepository.get_area_taxa(session, id_area)
        area = vmAreasRepository.get_area_info(session, id_area)
        if current_app.config["AFFICHAGE_MAILLE"]:
            observations = vmAreasRepository.last_observations_area_maille(
                session, current_app.config["NB_LAST_OBS"], id_area
            )
        else:
            observations = vmAreasRepository.last_observations_area_maille(
                session, current_app.config["NB_LAST_OBS"], id_area
            )

        observers = vmAreasRepository.get_observers_area(session, id_area)
        surroundingAreas = vmAreasRepository.get_surrounding_areas(session, id_area)
        session.close()
        connection.close()

        return render_template(
            "templates/areaSheet/_main.html",
            sheetType="area",
            surroundingAreas=surroundingAreas,
            listTaxons=listTaxons,
            areaInfos=area,
            observations=observations,
            observers=observers,
            DISPLAY_EYE_ON_LIST=True,
        )


# @main.route("/test", methods=["GET", "POST"])
# def test():
#    return render_template("templates/test.html")
