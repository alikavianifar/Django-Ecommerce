function addToCart(product_id) {

    //console.log(product_id)
    $.ajax({
        url: addToCartUrl,
        method: 'POST',
        data: {
            product_id: product_id,
            csrfmiddlewaretoken: csrfToken

        },
        success: function (response) {
            $("#total-cart-item-count").html(response.total_quantity)
            console.log(response);
            // do something with the response data
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log(errorThrown);
            // handle the error case
        }
    });
}
