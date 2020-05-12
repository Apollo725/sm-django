# encoding: utf-8

from __future__ import absolute_import
import logging
from django.forms import *
from django.forms.widgets import Input, Select
from django.utils.translation import ugettext_lazy as _
from sm.product.gsc import models
from sm.core.models import Country

logger = logging.getLogger(__name__)


class MaterializeForm(Form):
    error_css_class = "invalid"

    def is_valid(self):
        ret = super(MaterializeForm, self).is_valid()
        if self.is_bound:
            for f in self.errors:
                self.fields[f].widget.attrs.update(
                    {'class': self.fields[f].widget.attrs.get('class', '') \
                              + ' %s' % self.error_css_class})
        return ret

    def __init__(self, **kwargs):
        super(MaterializeForm, self).__init__(**kwargs)
        for field in self.fields:
            field = self.fields[field]
            if isinstance(field.widget, Input):
                if field.widget.is_required:
                    field.widget.attrs['required'] = ""
                    field.widget.attrs['data-parsley-trigger'] = "change"


class RegistrationForm(MaterializeForm):
    name = CharField(
        max_length=255,
        label=_("Full name"))

    contact_email = EmailField(
        max_length=255,
        label=_("Email address")
    )

    phone_number = CharField(
        max_length=255,
        label=_("Phone number"), required=True
    )

    reseller = CharField(
        max_length=255, required=False
    )

    def __init__(self, user, **kwargs):
        super(RegistrationForm, self).__init__(**kwargs)
        self.user = user
        self.vendor_profile = models.get_vendor_profile(user.customer)
        self.label_suffix = ""

    def save(self):
        user = self.user
        user.name = self.cleaned_data['name']
        user.contact_email = self.cleaned_data['contact_email']
        user.phone_number = self.cleaned_data['phone_number']
        user.save()

        reseller = self.cleaned_data['reseller']
        self.vendor_profile.reseller = reseller
        self.vendor_profile.save(update_fields=['reseller'])

    def get_initial(self):
        return {
            'name': self.user.name,
            'contact_email': self.user.contact_email or self.user.email,
            'phone_number': self.user.phone_number,
            'reseller': self.vendor_profile.reseller
        }


class OrderRequestForm(Form):
    plan = CharField(required=True)
    version = CharField(required=True)
    amount = IntegerField(required=True)


class ContactForm(MaterializeForm):
    name = CharField(required=True)
    contact_email = EmailField(required=True)
    phone_number = CharField(required=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        initial = kwargs.pop('initial', None)
        if not initial:
            initial = self.get_initial()
        super(ContactForm, self).__init__(initial=initial, **kwargs)

    def get_initial(self):
        return dict(
            name=self.user.name,
            contact_email=self.user.contact_email or self.user.email,
            phone_number=self.user.phone_number
        )

    def save(self):
        self.user.name = self.cleaned_data['name']
        self.user.contact_email = self.cleaned_data['contact_email']
        self.user.phone_number = self.cleaned_data['phone_number']
        self.user.save()
        return self.user

#
# ALL_COUNTRIES = [
#     ("", "--- Please select a country ---"),
#     ("Afghanistan", "Afghanistan (‫افغانستان‬‎)"),
#     ("Åland Islands", "Åland Islands (Åland)"),
#     ("Albania", "Albania (Shqipëri)"),
#     ("Algeria", "Algeria (‫الجزائر‬‎)"),
#     ("American Samoa", "American Samoa"),
#     ("Andorra", "Andorra"),
#     ("Angola", "Angola"),
#     ("Anguilla", "Anguilla"),
#     ("Antigua and Barbuda", "Antigua and Barbuda"),
#     ("Argentina", "Argentina"),
#     ("Armenia", "Armenia (Հայաստան)"),
#     ("Aruba", "Aruba"),
#     ("Australia", "Australia"),
#     ("Austria", "Austria (Österreich)"),
#     ("Azerbaijan", "Azerbaijan (Azərbaycan)"),
#     ("Bahamas", "Bahamas"),
#     ("Bahrain", "Bahrain (‫البحرين‬‎)"),
#     ("Bangladesh", "Bangladesh (বাংলাদেশ)"),
#     ("Barbados", "Barbados"),
#     ("Belarus", "Belarus (Беларусь)"),
#     ("Belgium", "Belgium (België)"),
#     ("Belize", "Belize"),
#     ("Benin", "Benin (Bénin)"),
#     ("Bermuda", "Bermuda"),
#     ("Bhutan", "Bhutan (འབྲུག)"),
#     ("Bolivia", "Bolivia"),
#     ("Bosnia and Herzegovina", "Bosnia and Herzegovina (Босна и Херцеговина)"),
#     ("Botswana", "Botswana"),
#     ("Brazil", "Brazil (Brasil)"),
#     ("British Indian Ocean Territory", "British Indian Ocean Territory"),
#     ("British Virgin Islands", "British Virgin Islands"),
#     ("Brunei", "Brunei"),
#     ("Bulgaria", "Bulgaria (България)"),
#     ("Burkina Faso", "Burkina Faso"),
#     ("Burundi", "Burundi (Uburundi)"),
#     ("Cambodia", "Cambodia (កម្ពុជា)"),
#     ("Cameroon", "Cameroon (Cameroun)"),
#     ("Canada", "Canada"),
#     ("Cape Verde", "Cape Verde (Kabu Verdi)"),
#     ("Caribbean Netherlands", "Caribbean Netherlands"),
#     ("Cayman Islands", "Cayman Islands"),
#     ("Central African Republic", "Central African Republic (République Centrafricaine)"),
#     ("Chad", "Chad (Tchad)"),
#     ("Chile", "Chile"),
#     ("China", "China (中国)"),
#     ("Christmas Island", "Christmas Island"),
#     ("Cocos (Keeling) Islands", "Cocos (Keeling) Islands (Kepulauan Cocos (Keeling))"),
#     ("Colombia", "Colombia"),
#     ("Comoros", "Comoros (‫جزر القمر‬‎)"),
#     ("Congo (DRC)", "Congo (DRC) (Jamhuri ya Kidemokrasia ya Kongo)"),
#     ("Congo (Republic)", "Congo (Republic) (Congo-Brazzaville)"),
#     ("Cook Islands", "Cook Islands"),
#     ("Costa Rica", "Costa Rica"),
#     ("Côte d’Ivoire", "Côte d’Ivoire"),
#     ("Croatia", "Croatia (Hrvatska)"),
#     ("Cuba", "Cuba"),
#     ("Curaçao", "Curaçao"),
#     ("Cyprus", "Cyprus (Κύπρος)"),
#     ("Czech Republic", "Czech Republic (Česká republika)"),
#     ("Denmark", "Denmark (Danmark)"),
#     ("Djibouti", "Djibouti"),
#     ("Dominica", "Dominica"),
#     ("Dominican Republic", "Dominican Republic (República Dominicana)"),
#     ("Ecuador", "Ecuador"),
#     ("Egypt", "Egypt (‫مصر‬‎)"),
#     ("El Salvador", "El Salvador"),
#     ("Equatorial Guinea", "Equatorial Guinea (Guinea Ecuatorial)"),
#     ("Eritrea", "Eritrea"),
#     ("Estonia", "Estonia (Eesti)"),
#     ("Ethiopia", "Ethiopia"),
#     ("Falkland Islands", "Falkland Islands (Islas Malvinas)"),
#     ("Faroe Islands", "Faroe Islands (Føroyar)"),
#     ("Fiji", "Fiji"),
#     ("Finland", "Finland (Suomi)"),
#     ("France", "France"),
#     ("French Guiana", "French Guiana (Guyane française)"),
#     ("French Polynesia", "French Polynesia (Polynésie française)"),
#     ("Gabon", "Gabon"),
#     ("Gambia", "Gambia"),
#     ("Georgia", "Georgia (საქართველო)"),
#     ("Germany", "Germany (Deutschland)"),
#     ("Ghana", "Ghana (Gaana)"),
#     ("Gibraltar", "Gibraltar"),
#     ("Greece", "Greece (Ελλάδα)"),
#     ("Greenland", "Greenland (Kalaallit Nunaat)"),
#     ("Grenada", "Grenada"),
#     ("Guadeloupe", "Guadeloupe"),
#     ("Guam", "Guam"),
#     ("Guatemala", "Guatemala"),
#     ("Guernsey", "Guernsey"),
#     ("Guinea", "Guinea (Guinée)"),
#     ("Guinea-Bissau", "Guinea-Bissau (Guiné Bissau)"),
#     ("Guyana", "Guyana"),
#     ("Haiti", "Haiti"),
#     ("Honduras", "Honduras"),
#     ("Hong Kong", "Hong Kong (香港)"),
#     ("Hungary", "Hungary (Magyarország)"),
#     ("Iceland", "Iceland (Ísland)"),
#     ("India", "India (भारत)"),
#     ("Indonesia", "Indonesia"),
#     ("Iran", "Iran (‫ایران‬‎)"),
#     ("Iraq", "Iraq (‫العراق‬‎)"),
#     ("Ireland", "Ireland"),
#     ("Isle of Man", "Isle of Man"),
#     ("Israel", "Israel (‫ישראל‬‎)"),
#     ("Italy", "Italy (Italia)"),
#     ("Jamaica", "Jamaica"),
#     ("Japan", "Japan (日本)"),
#     ("Jersey", "Jersey"),
#     ("Jordan", "Jordan (‫الأردن‬‎)"),
#     ("Kazakhstan", "Kazakhstan (Казахстан)"),
#     ("Kenya", "Kenya"),
#     ("Kiribati", "Kiribati"),
#     ("Kosovo", "Kosovo (Kosovë)"),
#     ("Kuwait", "Kuwait (‫الكويت‬‎)"),
#     ("Kyrgyzstan", "Kyrgyzstan (Кыргызстан)"),
#     ("Laos", "Laos (ລາວ)"),
#     ("Latvia", "Latvia (Latvija)"),
#     ("Lebanon", "Lebanon (‫لبنان‬‎)"),
#     ("Lesotho", "Lesotho"),
#     ("Liberia", "Liberia"),
#     ("Libya", "Libya (‫ليبيا‬‎)"),
#     ("Liechtenstein", "Liechtenstein"),
#     ("Lithuania", "Lithuania (Lietuva)"),
#     ("Luxembourg", "Luxembourg"),
#     ("Macau", "Macau (澳門)"),
#     ("Macedonia (FYROM)", "Macedonia (FYROM) (Македонија)"),
#     ("Madagascar", "Madagascar (Madagasikara)"),
#     ("Malawi", "Malawi"),
#     ("Malaysia", "Malaysia"),
#     ("Maldives", "Maldives"),
#     ("Mali", "Mali"),
#     ("Malta", "Malta"),
#     ("Marshall Islands", "Marshall Islands"),
#     ("Martinique", "Martinique"),
#     ("Mauritania", "Mauritania (‫موريتانيا‬‎)"),
#     ("Mauritius", "Mauritius (Moris)"),
#     ("Mayotte", "Mayotte"),
#     ("Mexico", "Mexico (México)"),
#     ("Micronesia", "Micronesia"),
#     ("Moldova", "Moldova (Republica Moldova)"),
#     ("Monaco", "Monaco"),
#     ("Mongolia", "Mongolia (Монгол)"),
#     ("Montenegro", "Montenegro (Crna Gora)"),
#     ("Montserrat", "Montserrat"),
#     ("Morocco", "Morocco (‫المغرب‬‎)"),
#     ("Mozambique", "Mozambique (Moçambique)"),
#     ("Myanmar (Burma)", "Myanmar (Burma) (မြန်မာ)"),
#     ("Namibia", "Namibia (Namibië)"),
#     ("Nauru", "Nauru"),
#     ("Nepal", "Nepal (नेपाल)"),
#     ("Netherlands", "Netherlands (Nederland)"),
#     ("New Caledonia", "New Caledonia (Nouvelle-Calédonie)"),
#     ("New Zealand", "New Zealand"),
#     ("Nicaragua", "Nicaragua"),
#     ("Niger", "Niger (Nijar)"),
#     ("Nigeria", "Nigeria"),
#     ("Niue", "Niue"),
#     ("Norfolk Island", "Norfolk Island"),
#     ("North Korea", "North Korea (조선 민주주의 인민 공화국)"),
#     ("Northern Mariana Islands", "Northern Mariana Islands"),
#     ("Norway", "Norway (Norge)"),
#     ("Oman", "Oman (‫عُمان‬‎)"),
#     ("Pakistan", "Pakistan (‫پاکستان‬‎)"),
#     ("Palau", "Palau"),
#     ("Palestine", "Palestine (‫فلسطين‬‎)"),
#     ("Panama", "Panama (Panamá)"),
#     ("Papua New Guinea", "Papua New Guinea"),
#     ("Paraguay", "Paraguay"),
#     ("Peru", "Peru (Perú)"),
#     ("Philippines", "Philippines"),
#     ("Pitcairn Islands", "Pitcairn Islands"),
#     ("Poland", "Poland (Polska)"),
#     ("Portugal", "Portugal"),
#     ("Puerto Rico", "Puerto Rico"),
#     ("Qatar", "Qatar (‫قطر‬‎)"),
#     ("Réunion", "Réunion (La Réunion)"),
#     ("Romania", "Romania (România)"),
#     ("Russia", "Russia (Россия)"),
#     ("Rwanda", "Rwanda"),
#     ("Saint Barthélemy", "Saint Barthélemy (Saint-Barthélemy)"),
#     ("Saint Helena", "Saint Helena"),
#     ("Saint Kitts and Nevis", "Saint Kitts and Nevis"),
#     ("Saint Lucia", "Saint Lucia"),
#     ("Saint Martin", "Saint Martin (Saint-Martin (partie française))"),
#     ("Saint Pierre and Miquelon", "Saint Pierre and Miquelon (Saint-Pierre-et-Miquelon)"),
#     ("Saint Vincent and the Grenadines", "Saint Vincent and the Grenadines"),
#     ("Samoa", "Samoa"),
#     ("San Marino", "San Marino"),
#     ("São Tomé and Príncipe", "São Tomé and Príncipe (São Tomé e Príncipe)"),
#     ("Saudi Arabia", "Saudi Arabia (‫المملكة العربية السعودية‬‎)"),
#     ("Senegal", "Senegal (Sénégal)"),
#     ("Serbia", "Serbia (Србија)"),
#     ("Seychelles", "Seychelles"),
#     ("Sierra Leone", "Sierra Leone"),
#     ("Singapore", "Singapore"),
#     ("Sint Maarten", "Sint Maarten"),
#     ("Slovakia", "Slovakia (Slovensko)"),
#     ("Slovenia", "Slovenia (Slovenija)"),
#     ("Solomon Islands", "Solomon Islands"),
#     ("Somalia", "Somalia (Soomaaliya)"),
#     ("South Africa", "South Africa"),
#     ("South Georgia & South Sandwich Islands", "South Georgia & South Sandwich Islands"),
#     ("South Korea", "South Korea (대한민국)"),
#     ("South Sudan", "South Sudan (‫جنوب السودان‬‎)"),
#     ("Spain", "Spain (España)"),
#     ("Sri Lanka", "Sri Lanka (ශ්‍රී ලංකාව)"),
#     ("Sudan", "Sudan (‫السودان‬‎)"),
#     ("Suriname", "Suriname"),
#     ("Svalbard and Jan Mayen", "Svalbard and Jan Mayen (Svalbard og Jan Mayen)"),
#     ("Swaziland", "Swaziland"),
#     ("Sweden", "Sweden (Sverige)"),
#     ("Switzerland", "Switzerland (Schweiz)"),
#     ("Syria", "Syria (‫سوريا‬‎)"),
#     ("Taiwan", "Taiwan (台灣)"),
#     ("Tajikistan", "Tajikistan"),
#     ("Tanzania", "Tanzania"),
#     ("Thailand", "Thailand (ไทย)"),
#     ("Timor-Leste", "Timor-Leste"),
#     ("Togo", "Togo"),
#     ("Tokelau", "Tokelau"),
#     ("Tonga", "Tonga"),
#     ("Trinidad and Tobago", "Trinidad and Tobago"),
#     ("Tunisia", "Tunisia (‫تونس‬‎)"),
#     ("Turkey", "Turkey (Türkiye)"),
#     ("Turkmenistan", "Turkmenistan"),
#     ("Turks and Caicos Islands", "Turks and Caicos Islands"),
#     ("Tuvalu", "Tuvalu"),
#     ("Uganda", "Uganda"),
#     ("Ukraine", "Ukraine (Україна)"),
#     ("United Arab Emirates", "United Arab Emirates (‫الإمارات العربية المتحدة‬‎)"),
#     ("United Kingdom", "United Kingdom"),
#     ("United States", "United States"),
#     ("U.S. Minor Outlying Islands", "U.S. Minor Outlying Islands"),
#     ("U.S. Virgin Islands", "U.S. Virgin Islands"),
#     ("Uruguay", "Uruguay"),
#     ("Uzbekistan", "Uzbekistan (Oʻzbekiston)"),
#     ("Vanuatu", "Vanuatu"),
#     ("Vatican City", "Vatican City (Città del Vaticano)"),
#     ("Venezuela", "Venezuela"),
#     ("Vietnam", "Vietnam (Việt Nam)"),
#     ("Wallis and Futuna", "Wallis and Futuna"),
#     ("Western Sahara", "Western Sahara (‫الصحراء الغربية‬‎)"),
#     ("Yemen", "Yemen (‫اليمن‬‎)"),
#     ("Zambia", "Zambia"),
#     ("Zimbabwe", "Zimbabwe")
# ]


ALL_COUNTRIES = [(country.name, u'{} ({})'.format(country.name, country.trans))
                 for country in Country.objects.all().order_by('name')]
ALL_COUNTRIES = [('', u'--- Please select a country ---')] + ALL_COUNTRIES


class BillingDetailForm(ModelForm):
    error_css_class = "invalid"

    def is_valid(self):
        ret = super(BillingDetailForm, self).is_valid()
        if self.is_bound:
            for f in self.errors:
                self.fields[f].widget.attrs.update(
                    {'class': self.fields[f].widget.attrs.get('class', '') \
                              + ' %s' % self.error_css_class})
        return ret

    def __init__(self, **kwargs):
        super(BillingDetailForm, self).__init__(**kwargs)
        for field in self.fields:
            field = self.fields[field]
            if isinstance(field.widget, (Input, Textarea)):
                if field.widget.is_required:
                    field.widget.attrs['required'] = ""
                    field.widget.attrs['data-parsley-trigger'] = "change"

    address = fields.CharField(
        widget=Textarea(attrs={'class': 'materialize-textarea'}), required=True
    )

    zip_code = fields.CharField(
        required=True, max_length=255
    )

    city = fields.CharField(
        required=True, max_length=255
    )

    state = fields.CharField(
        required=False, max_length=255,
    )

    country = fields.CharField(
        required=True, max_length=255, widget=Select(choices=ALL_COUNTRIES)
    )

    def clean(self):
        countries_with_states = ('Australia', 'Canada ', 'United States')
        data = self.cleaned_data
        if data.get('state', None) is None and data.get('country') in countries_with_states:
            raise ValidationError('State is required')
        else:
            return data

    def save(self, commit=True):
        ret = super(BillingDetailForm, self).save(commit)
        models.ProfileClazz.objects.update_or_create(profile=ret, product_clazz=models.PRODUCT_CLAZZ)
        return ret

    class Meta:
        model = models.Profile
        fields = ('address', 'zip_code', 'city', 'state', 'country')
