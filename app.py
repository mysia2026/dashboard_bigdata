import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="E-commerce Dashboard ", layout="wide")


# Wczytywanie i przygotowanie danych 

@st.cache_data
def load_data():
    orders = pd.read_csv('orders.csv')
    customers = pd.read_csv('customers.csv')
    items = pd.read_csv('items.csv')
    products = pd.read_csv('products.csv')
    payments = pd.read_csv('payments.csv')
    reviews = pd.read_csv('reviews.csv')

    # Przekształcanie kolumn na format daty
    orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'], errors='coerce')
    orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'], errors='coerce')
    orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'], errors='coerce')

    return orders, customers, items, products, payments, reviews


# Ładowanie danych
orders, customers, items, products, payments, reviews = load_data()


# Budowa Interfejsu Użytkownika 

st.title("Dashboard Olist E-commerce ")


st.markdown("### Główne Wskaźniki")

# Obliczenia do koszyka zamowien
basket_values = items.groupby('order_id')['price'].sum()
avg_basket = basket_values.mean()
max_basket = basket_values.max()
min_basket = basket_values.min()

# Spóźnione zamówienia
late_orders_mask = orders['order_delivered_customer_date'] > orders['order_estimated_delivery_date']
late_orders_count = late_orders_mask.sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Średnia wartość koszyka", f"{avg_basket:.2f} BRL")
col2.metric("Maksymalna wartość koszyka", f"{max_basket:.2f} BRL")
col3.metric("Mininalma wartość koszyka", f"{min_basket:.2f} BRL")
col4.metric("Spóźnione zamówienia", int(late_orders_count))

st.divider()

# Zakładki
tab1, tab2, tab3, tab4 = st.tabs(
    ["📦 Zamówienia i Klienci", "💰 Finanse i Płatności", "🏷️ Produkty i Kategorie", "⭐ Oceny i Recenzje"])

# --- ZAKŁADKA 1: ZAMÓWIENIA I KLIENCI ---
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Liczba zamówień w czasie")
        orders_monthly = orders.copy()
        orders_monthly['RokMiesiac'] = orders_monthly['order_purchase_timestamp'].dt.to_period('M').astype(str)
        monthly_counts = orders_monthly.groupby('RokMiesiac').size().reset_index(name='liczba_zamowien')

        fig_monthly = px.line(monthly_counts, x="RokMiesiac", y="liczba_zamowien", markers=True,
                              title="Miesięczny trend zamówień")
        st.plotly_chart(fig_monthly, use_container_width=True)

        st.subheader("Top 10 Miast wg klientów")
        top_cities = customers['customer_city'].value_counts().head(10).reset_index()
        top_cities.columns = ['Miasto', 'Liczba klientów']

        fig_cities = px.bar(top_cities, x='Miasto', y='Liczba klientów')
        st.plotly_chart(fig_cities, use_container_width=True)

    with col_b:
        st.subheader("Statusy zamówień")
        order_statuses = orders['order_status'].value_counts().reset_index()
        order_statuses.columns = ['Status', 'Liczba zamówień']

        fig_status = px.pie(order_statuses, values='Liczba zamówień', names='Status', hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)

        st.subheader("Rozkład liczby produktów w zamówieniu")
        items_per_order = items.groupby('order_id').size().value_counts().reset_index()
        items_per_order.columns = ['Liczba produktów', 'Liczba zamówień']
        items_per_order = items_per_order.sort_values('Liczba produktów')

        fig_items = px.bar(items_per_order, x='Liczba produktów', y='Liczba zamówień')
        st.plotly_chart(fig_items, use_container_width=True)

# --- ZAKŁADKA 2: FINANSE I PŁATNOŚCI ---
with tab2:
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Udział metod płatności")
        payment_shares = payments['payment_type'].value_counts(normalize=True).reset_index()
        payment_shares.columns = ['Typ', 'Procent']
        payment_shares['Procent'] *= 100

        fig_pay_share = px.pie(payment_shares, values='Procent', names='Typ')
        st.plotly_chart(fig_pay_share, use_container_width=True)

    with col_d:
        st.subheader("Średnia wartość dla typu płatności")
        avg_payment = payments.groupby('payment_type')['payment_value'].mean().reset_index().sort_values(
            'payment_value', ascending=False)
        avg_payment.columns = ['Typ płatności', 'Średnia Kwota']

        fig_avg_pay = px.bar(avg_payment, x='Typ płatności', y='Średnia Kwota')
        st.plotly_chart(fig_avg_pay, use_container_width=True)

    st.subheader("Top 10 Klientów (Największy przychód)")
    orders_payments = pd.merge(orders[['order_id', 'customer_id']], payments[['order_id', 'payment_value']],
                               on='order_id', how='inner')
    top_customers = orders_payments.groupby('customer_id').agg(
        Wydana_Kwota=('payment_value', 'sum'),
        Liczba_Zamówień=('order_id', 'count')
    ).reset_index().sort_values('Wydana_Kwota', ascending=False).head(10)

    st.dataframe(top_customers, use_container_width=True)

# --- ZAKŁADKA 3: PRODUKTY I KATEGORIE ---
with tab3:

    items_products = pd.merge(items, products, on='product_id', how='inner')

    col_e, col_f = st.columns(2)

    with col_e:
        st.subheader("Top 10 najlepiej sprzedających się produktów")
        top_products = items_products['product_id'].value_counts().head(10).reset_index()
        top_products.columns = ['product_id', 'total_sold']
        top_products_info = pd.merge(top_products, products[['product_id', 'product_category_name']], on='product_id',
                                     how='left')

        st.dataframe(top_products_info, use_container_width=True)

        st.subheader("Najpopularniejsze kategorie")
        pop_cats = items_products['product_category_name'].value_counts().head(10).reset_index()
        pop_cats.columns = ['Kategoria', 'Liczba sprzedanych']

        fig_pop_cats = px.bar(pop_cats, x='Liczba sprzedanych', y='Kategoria', orientation='h').update_layout(
            yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_pop_cats, use_container_width=True)

    with col_f:
        st.subheader("Kategorie generujące największy przychód")
        cat_revenue = items_products.groupby('product_category_name')['price'].sum().reset_index().sort_values('price',
                                                                                                               ascending=False).head(
            10)
        cat_revenue.columns = ['Kategoria', 'Przychód']

        fig_cat_rev = px.bar(cat_revenue, x='Kategoria', y='Przychód')
        st.plotly_chart(fig_cat_rev, use_container_width=True)

# --- ZAKŁADKA 4: OCENY I RECENZJE ---
with tab4:

    reviews_items = pd.merge(reviews[['order_id', 'review_score']], items[['order_id', 'product_id']], on='order_id',
                             how='inner')
    reviews_full = pd.merge(reviews_items, products[['product_id', 'product_category_name']], on='product_id',
                            how='inner')

    avg_reviews = reviews_full.groupby('product_category_name')['review_score'].mean().reset_index()

    col_g, col_h = st.columns(2)

    with col_g:
        st.subheader("Najlepiej oceniane kategorie")
        best_cats = avg_reviews.sort_values('review_score', ascending=False).head(10)
        best_cats.columns = ['Kategoria', 'Średnia Ocena']
        st.dataframe(best_cats, use_container_width=True)

    with col_h:
        st.subheader("Najgorzej oceniane kategorie")
        worst_cats = avg_reviews.sort_values('review_score', ascending=True).head(10)
        worst_cats.columns = ['Kategoria', 'Średnia Ocena']
        st.dataframe(worst_cats, use_container_width=True)
