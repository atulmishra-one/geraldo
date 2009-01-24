import copy, types

from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

BAND_WIDTH = 'band-width'
BAND_HEIGHT = 'band-height'

def landscape(page_size):
    return page_size[1], page_size[0]

def get_attr_value(obj, attr):
    """This function returns a value from a object doesn't matters if the
    attribute is a function or not"""
    value = getattr(obj, attr)
    
    if type(value) == types.MethodType:
        return value()

    return value

class BaseReport(object):
    """Basic Report class, inherited and used to make reports adn subreports"""

    # Bands - is not possible to have more than one band from the same kind
    band_begin = None
    band_summary = None
    band_page_header = None
    band_page_footer = None
    band_detail = None
    groups = None

    # Data source driver
    queryset = None
    print_if_empty = False # This means if a queryset is empty, the report will
                           # be generated or not

    # Style and colors
    default_font_color = black
    default_stroke_color = black
    default_fill_color = black
    borders = None

    def __init__(self, queryset=None):
        self.queryset = queryset or self.queryset
        self.groups = self.groups or []

    def get_objects_list(self):
        """Returns the list with objects to be rendered.
        
        This should be refactored in the future to support big amounts of
        records."""
        if not self.queryset:
            return []

        return [object for object in self.queryset]

    def format_date(self, date, expression):
        """Use a date format string method to return formatted datetime"""
        return date.strftime(expression)

class Report(BaseReport):
    """This class must be inherited to be used as a new report.
    
    A report has bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to work properly"""
    # Report properties
    title = ''
    author = ''
    
    # Page dimensions
    page_size = A4
    margin_top = 1*cm
    margin_bottom = 1*cm
    margin_left = 1*cm
    margin_right = 1*cm
    _page_rect = None

    # SubReports
    subreports = None

    default_style = None

    def __init__(self, queryset=None):
        super(Report, self).__init__(queryset)

        self.subreports = self.subreports or []
        self.default_style = self.default_style or {}

    def generate_by(self, generator_class, *args, **kwargs):
        """This method uses a generator inherited class to generate a report
        to a desired format, like XML, HTML or PDF, for example.
        
        The arguments *args and **kwargs are passed to class initializer."""
        generator = generator_class(self, *args, **kwargs)

        return generator.execute()

    def get_page_rect(self):
        """Calculates a dictionary with page dimensions inside the margins
        and returns. It is used to make page borders."""
        if not self._page_rect:
            client_width = self.page_size[0] - self.margin_left - self.margin_right
            client_height = self.page_size[1] - self.margin_top - self.margin_bottom

            self._page_rect = {
                'left': self.margin_left,
                'top': self.margin_top,
                'right': self.page_size[0] - self.margin_right,
                'bottom': self.page_size[1] - self.margin_bottom,
                'width': client_width,
                'height': client_height,
                }

        return self._page_rect


class SubReport(BaseReport):
    """Class to be used for subreport objects. It doesn't need to be inherited.
    
    'queryset_string' must be a string with path for Python compatible queryset.
    
    Examples:
    
        * '%(object)s.user_permissions.all()'
        * '%(object)s.groups.all()'
        * 'Message.objects.filter(user=%(object)s)'
        * 'Message.objects.filter(user__id=%(object)s.id)'
    """
    _queryset_string = None
    _parent_object = None
    _queryset = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @property
    def queryset(self):
        if not self._queryset and self.parent_object and self.queryset_string:
            # Replaces the string representer to a local variable identifier
            queryset_string = self.queryset_string%{'object': 'parent_object'}

            # Loads the queryset from string
            self._queryset = eval(
                    queryset_string,
                    {'parent_object': self.parent_object},
                    )

        return self._queryset

    def _get_parent_object(self):
        return self._parent_object

    def _set_parent_object(self, value):
        # Clears queryset
        self._queryset = None
        self._parent_object = value

    parent_object = property(_get_parent_object, _set_parent_object)

    def _get_queryset_string(self):
        return self._queryset_string

    def _set_queryset_string(self, value):
        # Clears queryset
        self._queryset = None
        self._queryset_string = value

    queryset_string = property(_get_queryset_string, _set_queryset_string)

class ReportBand(object):
    """A band is a horizontal area in the report. It can be used to print
    things on the top, on summary, on page header, on page footer or one time
    per object from queryset."""
    height = 1*cm
    visible = True
    borders = {'top': None, 'right': None, 'bottom': None, 'left': None,
            'all': None}
    elements = None
    child_bands = None
    force_new_page = False
    default_style = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        self.elements = self.elements or []
        self.child_bands = self.child_bands or []
        self.default_style = self.default_style or {}

    def clone(self):
        """Does a deep copy of this band to be rendered"""
        return copy.deepcopy(self)

class TableBand(ReportBand): # TODO
    """This band must be used only as a detail band. It doesn't is repeated per
    object, but instead of it is streched and have its rows increased."""
    pass

class ReportGroup(object):
    """This a report grouper class. A report can be multiple groupped by
    attribute values."""
    attribute_name = None
    band_header = None
    band_footer = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class Element(object):
    """The base class for widgets and graphics"""
    _width = 0
    _height = 0

    # 'width' property
    def _get_width(self):
        if self._width == BAND_WIDTH and self.band:
            return self.band.width

        return self._width

    def _set_width(self, value):
        self._width = value

    width = property(_get_width, _set_width)

    # 'height' property
    def _get_height(self):
        if self._height == BAND_HEIGHT and self.band:
            return self.band.height

        return self._height

    def _set_height(self, value):
        self._height = value

    height = property(_get_height, _set_height)

