from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


class CustomPaginator(Paginator):

    def get_objects(self, page):
        try:
            orders = self.page(page)
        except PageNotAnInteger:
            orders = self.page(1)
        except EmptyPage:
            orders = self.page(self.num_pages)
        return orders
