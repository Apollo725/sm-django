# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging

from dateutil.relativedelta import relativedelta
from django.core import management
from django.utils import timezone
from faker import Factory

from sm.core.utils.model_utils import create_display_products_from_product
from sm.product.gsc.models import *

fake = Factory.create()
logger = logging.getLogger(__name__)

GAE_CUSTOMER_NAME = 'foo.com'
GAE_ADMIN_NAME = 'admin'
GAE_ADMIN_EMAIL = "@".join([GAE_ADMIN_NAME, GAE_CUSTOMER_NAME])

origin_price_list = [
    (5, 50.0),
    (10, 100.0),
    (20, 200.0),
    (50, 250.0),
    (100, 350.0),
    (500, 450.0),
    (1000, 550.0),
    (99999, 1250.0),
    # production version, yearly price, monthly price
    (ProductVersionEnum.BASIC, 9.48, 1.00),
    (ProductVersionEnum.PRO, 12.00, 1.29),
    (ProductVersionEnum.ENTERPRISE, 15.48, 1.49),
]

vendor = [
    [1, 'GSC'],
    [2, 'Google']
]

product_category = [
    [1, 'GSC', 'Shared Contacts for G Suite', 1, None],
    [2, 'GSC_GMAIL', 'Shared Contacts for Gmail', 1, None],
    [3, 'GSUITE', 'G Suite', 2, None],
    [4, 'GDRIVE', 'Google Drive', 2, 3],
    [5, 'GVAULT', 'Google Vault', 2, 3],
    [6, 'CDM', 'Chromebox device management', 1, None],
    [7, 'GAMS', 'Google Apps message security', 1, None],
]

product_versions = [
    {
        'id': 1,
        'codename': 'BASIC',
        'name': 'Basic',
        'extended_name': 'Basic Edition',
        'color_code': '#AAAAAA',
        'motto': 'Pack of 5 users',
        'sku': 'GSUITE_BASIC',
        'product_category_id': 1,
    },
    {
        'id': 2,
        'codename': 'PRO',
        'name': 'Pro',
        'extended_name': 'Professional Edition',
        'color_code': '#2A9621',
        'motto': 'Unlimited Sharing',
        'sku': 'GSUITE_PRO',
        'product_category_id': 1,
    },
    {
        'id': 3,
        'codename': 'BUSINESS',
        'name': 'Business',
        'extended_name': 'Corporate Edition',
        'color_code': '#D18136',
        'motto': 'Advanced Enterprise Capabilities',
        'sku': 'GSUITE_BUSINESS',
        'product_category_id': 1,
    },
    {
        'id': 4,
        'codename': 'ENTERPRISE',
        'name': 'Enterprise',
        'extended_name': 'Enterprise Edition',
        'color_code': '#3369BF',
        'motto': 'Sharing with any type of account',
        'sku': 'GSUITE_ENTERPRISE',
        'product_category_id': 1,
    },
    {
        'id': 5,
        'codename': 'FREE',
        'name': 'Free',
        'extended_name': 'Free Edition',
        'color_code': '#6F4F87',
        'motto': '',
        'sku': 'GSUITE_FREE',
        'product_category_id': 1,
    },
    {
        'id': 6,
        'codename': 'EVALUATION',
        'name': 'Eval',
        'extended_name': 'Evaluation version',
        'color_code': '#3FC9CC',
        'motto': '',
        'sku': 'GSUITE_EVALUATION',
        'product_category_id': 1,
    },
    {
        'id': 7,
        'codename': 'EDUCATION',
        'name': 'Education',
        'extended_name': 'Education version',
        'color_code': '#3FC9CC',
        'motto': '',
        'sku': 'GSUITE_EDUCATION',
        'product_category_id': 1,
    },
]

product_features = [
    {
        'id': 1,
        'name': 'Number of shared contacts',
        'product_category': 1,
    },
    {
        'id': 2,
        'name': 'Unlimited Support',
        'product_category': 1,
    },
    {
        'id': 3,
        'name': '24/7 technical support',
        'product_category': 1,
    },
    {
        'id': 4,
        'name': 'Mobile/Tablet & Outlook sync',
        'product_category': 1,
    },
    {
        'id': 5,
        'name': 'Advanced logging and security features',
        'product_category': 1,
    },
    {
        'id': 6,
        'name': 'Sharing with users and users groups',
        'product_category': 1,
    },
    {
        'id': 7,
        'name': 'Permission delegation',
        'product_category': 1,
    },
    {
        'id': 8,
        'name': 'Sharing with external domain users and @gmail.com addresses',
        'product_category': 1,
    },
    {
        'id': 9,
        'name': 'Sharing with users',
        'product_category': 1,
    },
]

feature_version_options = [
    # feature, version, bold, position
    [1, 1, False, 1],
    [1, 6, False, 2],
    [1, 7, False, 3],

    [2, 2, False, 1],
    [2, 3, False, 2],

    [3, 1, False, 1],
    [3, 2, False, 2],
    [3, 3, False, 3],
    [3, 4, False, 4],

    [4, 1, False, 1],
    [4, 2, False, 2],
    [4, 3, False, 3],
    [4, 4, False, 4],
    [4, 5, False, 5],
    [4, 6, False, 6],
    [4, 7, False, 7],

    [5, 4, False, 1],

    [6, 3, False, 1],
    [6, 4, False, 2],
    [6, 6, False, 3],
    [6, 7, False, 4],

    [7, 1, False, 1],
    [7, 2, False, 2],
    [7, 4, False, 3],

    [8, 4, False, 1],

    [9, 1, False, 1],
    [9, 2, False, 2],
    [9, 3, False, 3],
    [9, 4, False, 4],
    [9, 5, False, 5],
    [9, 6, False, 6],
    [9, 7, False, 7],
]

feature_product_category_options = [
    # feature, product category, bold, position
]

product_plans = [
    {
        'id': 1,
        'name': 'Flexible',
        'codename': SubscriptionPlan.FLEXIBLE,
        'toggle_name': 'Monthly',
        'full_name': 'Monthly Plan',
        'description': 'billed monthly',
        'alternate_frequency': '',
        'billing_frequency': FrequencyEnum.MONTH,
        'commitment': '',
        'billing_cycle': BillingCycleEnum.END_OF_MONTH,
    },
    {
        'id': 2,
        'name': 'Annual yearly',
        'codename': SubscriptionPlan.ANNUAL_YEARLY,
        'toggle_name': 'Yearly',
        'full_name': 'Yearly Plan',
        'description': 'billed annualy',
        'alternate_frequency': FrequencyEnum.MONTH,
        'billing_frequency': FrequencyEnum.YEAR,
        'commitment': FrequencyEnum.YEAR,
        'billing_cycle': BillingCycleEnum.DATE_TO_DATE,
    },
    {
        'id': 3,
        'name': 'Annual monthly',
        'codename': SubscriptionPlan.ANNUAL_MONTHLY,
        'toggle_name': 'Monthly',
        'full_name': 'Monthly Plan (annual commitment)',
        'description': 'billed monthly',
        'alternate_frequency': FrequencyEnum.YEAR,
        'billing_frequency': FrequencyEnum.MONTH,
        'commitment': FrequencyEnum.MONTH,
        'billing_cycle': BillingCycleEnum.END_OF_MONTH,
    },
    {
        'id': 4,
        'name': 'Flex prepaid',
        'codename': SubscriptionPlan.FLEX_PREPAID,
        'toggle_name': 'Monthly',
        'full_name': 'Monthly Plan',
        'description': 'billed monthly',
        'alternate_frequency': '',
        'billing_frequency': FrequencyEnum.MONTH,
        'commitment': FrequencyEnum.MONTH,
        'billing_cycle': BillingCycleEnum.DATE_TO_DATE,
    },
]


def add_vendor():
    for item in vendor:
        id, name = item
        Vendor.objects.update_or_create(dict(
            id = id,
            name = name
        ), id = id)


def add_product_category():
    add_vendor()
    for category in product_category:
        id, code, name, vendor, parent_category = category

        ProductCategory.objects.update_or_create(
            {
                'id': id,
                'code': code,
                'name': name,
                'vendor_id': vendor,
                'parent_category_id': parent_category,
            },
            id=id
        )


def add_default_catalog():
    add_catalog(
        oid=2,
        name="GSC Standard prices",
        basic_price=50.0,
        price_list=origin_price_list,
        default=True
    )


def add_discount_catalogs():
    origin_basic_price = 50.0

    def _add_discount_catalog(name, discount, oid):
        price_list = []
        for price in origin_price_list:
            if not isinstance(price[0], ProductVersionEnum):
                tier, pricing = price
                price_list.append((tier, pricing * (1 - discount)))
            else:
                version, yearly, monthly = price
                price_list.append((version, yearly * (1 - discount), monthly))

        add_catalog(
            oid=oid,
            name=name,
            basic_price=origin_basic_price * (1 - discount),
            price_list=price_list,
        )

    _add_discount_catalog(
        'GSC -50% Discount', 0.5, 3
    )

    _add_discount_catalog(
        'GSC -20% Reseller Discount', 0.2, 6
    )

    _add_discount_catalog(
        'GSC -20% Discount', 0.2, 12
    )

    _add_discount_catalog(
        'GSC -15% Promotional Code', 0.15, 14
    )

    _add_discount_catalog(
        'GSC -30% Non-Profit Code', 0.3, 15
    )

    def add_econsulting_catalog():
        price_list = [
            (5, 9.0),
            (10, 9.0),
            (20, 9.0),
            (50, 150.0),
            (100, 150.0),
            (500, 150.0),
            (1000, 150.0),
            (99999, 150.0)
        ]

        add_catalog(
            oid=1,
            name="Econsulting",
            basic_price=9.0,
            price_list=price_list,
        )

    add_econsulting_catalog()


def create_fake_profile(customer):
    profile, _ = Profile.objects.update_or_create(
        dict(
            address=fake.address(),
            city=fake.city(),
            state=fake.state(),
            country=fake.country(),
            zip_code=fake.zipcode()
        ), customer=customer)

    ProfileClazz.objects.update_or_create(dict(
        product_clazz=PRODUCT_CLAZZ
    ), profile=profile)

    user = customer.get_communication_user()
    user.phone_number = fake.phone_number()
    user.save()


def add_product_versions():
    for version in product_versions:
        ProductVersion.objects.get_or_create(**version)


def add_product_features():
    for feature in product_features:
        product_category = ProductCategory.objects.get(
            id=feature['product_category']
        )
        instance, is_created = ProductFeature.objects.get_or_create(
                id=feature['id'],
                name=feature['name'],
                product_category=product_category,
        )


def add_feature_version_options():
    for option in feature_version_options:
        feature_id, version_id, is_bold, position = option
        FeatureVersion.objects.get_or_create(
            feature_id=feature_id,
            version_id=version_id,
            bold=is_bold,
            position=position,
        )


def add_feature_product_category_options():
    for option in feature_product_category_options:
        feature_id, product_category_id, is_bold, position = option
        FeatureProductCategory.objects.get_or_create(
            feature_id=feature_id,
            product_category_id=product_category_id,
            bold=is_bold,
            position=position,
        )


def add_product_plans():
    for plan in product_plans:
        ProductPlan.objects.get_or_create(**plan)


def add_extra_products():
    product_category = ProductCategory.objects.get(code='GSUITE')
    Product.objects.get_or_create(
        {
            'code': 'GSUITE_PREMIER_NO_PLAN',
            'name': 'GSUITE premier no plan',
            'category': product_category,
            'vendor_sku': '',
            'version': ProductVersion.objects.get(codename='BUSINESS'),
            'tier_number': 100,
            'tier_name': '1-100',
        },
        code='GSUITE_PREMIER_NO_PLAN'
    )
    Product.objects.get_or_create(
        {
            'code': 'GSUITE_EDU_NO_PLAN',
            'name': 'GSUITE edu no plan',
            'category': product_category,
            'vendor_sku': '',
            'version': ProductVersion.objects.get(codename='EDUCATION'),
            'tier_number': 100,
            'tier_name': '1-100',
        },
        code='GSUITE_EDU_NO_PLAN'
    )
    Product.objects.get_or_create(
        {
            'code': 'GSUITE_BASIC_NO_PLAN',
            'name': 'GSUITE basic no plan',
            'category': product_category,
            'vendor_sku': '',
            'version': ProductVersion.objects.get(codename='BASIC'),
            'tier_number': 100,
            'tier_name': '1-100',
        },
        code='GSUITE_BASIC_NO_PLAN'
    )
    Product.objects.get_or_create(
        {
            'code': 'GSUITE_FREE_NO_PLAN',
            'name': 'GSUITE free no plan',
            'category': product_category,
            'vendor_sku': '',
            'version': ProductVersion.objects.get(codename='FREE'),
            'tier_number': 100,
            'tier_name': '1-100',
        },
        code='GSUITE_FREE_NO_PLAN'
    )


def add_display_products():
    for product in Product.objects.all():
        create_display_products_from_product(product)


def add_countries():
    Country.objects.get_or_create(
        {
            'name': 'United States of America',
            'currency': 'USD',
            'continent': 'North America',
            'trans': 'United States of America'
        },
        code='USA'
    )
    Country.objects.get_or_create(
        {
            'name': 'China',
            'currency': 'CNY',
            'continent': 'Asia',
            'trans': u'中國'
        },
        code='CHN'
    )


def update_product_category():
    # add default products to category
    product_categories = ProductCategory.objects.filter(
        default_product__isnull=True
    )
    for category in product_categories:
        product = category.products.order_by('id').first() \
                  or Product.objects.order_by('id').first()
        category.default_product = product
        category.save()


def mock():
    if settings.TEST_MODE:
        management.call_command('loaddata', 'mocks.json')
        logger.info("mock data for products, catalogs, product_catalogs is added")
        return

    add_product_category()
    add_product_plans()
    add_product_features()
    add_product_versions()
    add_feature_version_options()
    add_feature_product_category_options()
    add_default_catalog()
    add_discount_catalogs()
    add_extra_products()
    add_display_products()
    add_countries()

    update_product_category()

    # add customers
    for info in [
        # name, domain, user_number, renewal_option
        ['admin', 'test-1.com', 13, RenewalOption.CANCEL,
            'new customer, 13 users, eval'],
        ['admin', 'test-2.com', 5, RenewalOption.RENEW,
            'paid customer, 5 users, basic plan, monthly payment'],
        ['admin', 'test-3.com', 8, RenewalOption.RENEW,
            'paid customer, 8 users, pro plan, yearly payment'],
        ['admin', 'test-4.com', 20, RenewalOption.RENEW,
         'paid customer, 20 users, per user, pro plan, monthly payment'],
        ['admin', 'test-5.com', 15, RenewalOption.RENEW,
            'paid customer 20 users pack, pro plan, yearly payment'],
        ['admin', 'test-6.com', 90, RenewalOption.RENEW,
         'paid customer 100 users pack, pro plan, yearly payment']
    ]:
        name, domain, user_number, renewal_option, description = info
        email = '@'.join([name, domain])
        name = ' '.join([name, domain])
        customer, _ = Customer.objects.update_or_create({}, name=domain)

        user, _ = User.objects.update_or_create(
            dict(name=name, mock=True,
                 description=description),
            email=email,
            customer=customer,
        )

        vendor_profile, _ = VendorProfile.objects.update_or_create(
            {
                'users': user_number,
                'org_name': domain,
                'apps_version': 'basic',
                'country': 'USA'
            },
            customer=customer, name=domain)

        VendorProfileClazz.objects.update_or_create(
            vendor_profile=vendor_profile,
            product_clazz=PRODUCT_CLAZZ
        )

        subscription = SubscriptionManager(customer).ensure_exists()
        subscription.renewal_option = renewal_option
        subscription.billing_cycle_start = timezone.now()
        subscription.billing_cycle_end = relativedelta(years=1) + timezone.now()
        subscription.add_order = SubscriptionOrderAddStrategy.EXTEND
        subscription.upgrade_order = SubscriptionOrderUpgradeStrategy.EXTEND
        if subscription.renewal_option == RenewalOption.RENEW:
            create_fake_profile(customer)
            subscription.vendor_licenses = user_number
            if user_number == 15:
                tier = subscription.catalog.get_tier(user_number,
                                                     version=ProductVersionEnum.PRO,
                                                     plan=SubscriptionPlan.ANNUAL_YEARLY)
                subscription.expiry_date = relativedelta(
                    years=1) + timezone.now()
                sub_total = tier.price
                subscription.vendor_licenses = tier.product.tier_number
                subscription.vendor_status = VendorStatus.PAID
            elif user_number == 20:
                tier = subscription.catalog.get_tier(-1,
                                                     version=ProductVersionEnum.PRO,
                                                     plan=SubscriptionPlan.FLEX_PREPAID)
                subscription.expiry_date = relativedelta(
                    months=1) + timezone.now()
                subscription.vendor_licenses = 15
                sub_total = tier.price * subscription.vendor_licenses
                subscription.vendor_status = VendorStatus.PAID
            elif user_number == 8:
                tier = subscription.catalog.get_tier(8,
                                                     version=ProductVersionEnum.PRO,
                                                     plan=SubscriptionPlan.ANNUAL_YEARLY)
                subscription.expiry_date = relativedelta(
                    years=1) + timezone.now()
                subscription.vendor_licenses = 10
                sub_total = tier.price
                subscription.vendor_status = VendorStatus.PAID
            elif user_number == 5:
                tier = subscription.catalog.get_tier(5,
                                                     version=ProductVersionEnum.BASIC,
                                                     plan=SubscriptionPlan.FLEX_PREPAID)
                subscription.expiry_date = relativedelta(
                    months=1) + timezone.now()
                subscription.vendor_licenses = 5
                sub_total = tier.price
                subscription.vendor_status = VendorStatus.PAID
            elif user_number == 90:
                tier = subscription.catalog.get_tier(user_number,
                                                     version=ProductVersionEnum.PRO,
                                                     plan=SubscriptionPlan.FLEX_PREPAID)
                subscription.expiry_date = relativedelta(
                    months=1) + timezone.now()
                subscription.vendor_licenses = tier.product.tier_number
                sub_total = tier.price
                subscription.vendor_status = VendorStatus.PAID
            else:
                continue

            subscription.product = tier.product
            order, _ = Order.objects.update_or_create(
                {
                    "name": 'order for %s' % customer,
                    "currency": customer.currency,
                    "status": OrderStatus.PAID
                },
                status=OrderStatus.PAID,
                customer=customer,
            )

            OrderDetail.objects.update_or_create(
                {
                    'product': subscription.product,
                    'catalog': subscription.catalog,
                    'subscription': subscription,
                    'sub_total': sub_total
                },
                order=order
            )

            subscription.order = order
            # Creating DRAFT order
            order, _ = Order.objects.update_or_create(
                {
                    "name": 'draft order for %s' % customer,
                    "currency": customer.currency,
                },
                status=OrderStatus.DRAFT,
                customer=customer
            )

            OrderDetail.objects.update_or_create(
                {
                    'product': subscription.product,
                    'catalog': subscription.catalog,
                    'subscription': subscription,
                    'sub_total': sub_total,
                    'status': OrderStatus.DRAFT,
                    'type': OrderDetailType.NEW,
                },
                order=order
            )
        subscription.save()

    # add promotion code
    PromotionCode.objects.update_or_create(
        dict(
           catalog=Catalog.objects.get(name="GSC -15% Promotional Code")
        ), code='7152214'
    )
