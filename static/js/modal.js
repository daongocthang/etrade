$(document).ready(function () {
    $('#basicModal').on('hidden.bs.modal', function () {
        $(this).find('form').trigger('reset');
    });

    $('.bt-order').click(function () {
        $('#mdTitle').empty();
        $('#mdTitle').append($(this).data('status') == 'sell' ? 'BÁN' : 'MUA');

        $('#ftSymbol').val($(this).data('symbol'));
        $('#ftStatus').val($(this).data('status') == 'sell' ? 'sell' : 'buy');
    });

    $('#btCarryOut').click(function () {
        let symbol = $('#ftSymbol').val();
        let volume = $('#ftVolume').val();
        let price = $('#ftPrice').val();
        let status = $('#ftStatus').val();

        if (symbol == '' || volume == '' || price == '') {
            alert('All fields are required')
        }

        $.ajax({
            url: "/transaction",
            method: "POST",
            data: {symbol: symbol, volume: volume, price: price, status: status},
            success: function (data) {
                if (data == 'ok') {
                    $('#basicModal').hide();
                    location.reload();
                }
                else {
                    alert("Something is wrong");
                }
            }
        });
    });
});