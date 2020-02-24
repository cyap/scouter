$( () => {
    addSorting();
    addExport();
});

function addSorting() {
  let s = new Sortable($('tbody')[0], {
    animation: 150
  });

  $('tr').each((i, el) => {
    new Sortable(el, {
        draggable: '.pokemon',
        animation: 150
    });
  });

  $('.remove-button').click( (e, f) => {
    $(e.target.parentNode.parentNode).remove();
  });
}


function addExport() {
  // Serialization
  $('#export').click(() => {
    let urls = $('tr a').map((a, b) => b.href);
    let children = $('tr').map((a, b) => $(b).find('.pokemon'));
    let res = urls.map((i, url) => {
      return {
        'url': url,
        'team': Array.from(children[i]).slice(2).map((a, b) => $(a).data('pokemon'))
      };
    });
    $('#serialization').html(JSON.stringify([...res]));
  });
}
