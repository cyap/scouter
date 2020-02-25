$( () => {
    addSorting();
    addExport();
    addExpand();

    const history = []
    addHide(history);
    addUndo(history);

    addSave();
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

}

function addHide(history) {
  // Change to hide
  $('.remove-button').click( (e, f) => {
    let row = $(e.target.parentNode.parentNode);
    row.toggle();
    history.push(row);
  });
}

function addUndo(history) {
  $('#undo').click( (e, f) => {
     if (!history) return;
     let row = history.pop();
     row.toggle();
  })
}

function serialize() {
  let rows = $('tr').filter((i, node) => $(node).css('display') !== 'none');
  let urls = rows.find('a').map((a, b) => b.href);
  let children = rows.map((a, b) => $(b).find('.pokemon'));
  let players = rows.map((a, b) => $(b).data('player-num'))
  let res = urls.map((i, url) => {
    return {
      'url': url,
      'team': Array.from(children[i]).map((a, b) => $(a).data('pokemon')),
      'player': players[i]
    };
  });
  return JSON.stringify([...res]);
}

function addExport() {
  $('#export').click(() => { $('#serialization').html(serialize()); });
}

function addExpand() {
  $('.expand-button').click((e, f) => {
    if (!$(e.target).hasClass('expanded')) {
      expandRow($(e.target));
    }
    else {
      compressRow($(e.target));
    }
  });

  $('#expand-all').click((e, f) => {
    let transform = $(e.target).hasClass('expanded') ? compressRow : expandRow;
    let text = $(e.target).hasClass('expanded') ? 'Expand All' : 'Compress All';
    $('.expand-button').each((i, button) => { transform($(button)); });
    $(e.target).text(text);
    $(e.target).toggleClass('expanded');
  });
}

function expandRow(button) {
  if ($(button).hasClass('expanded')) return;
  let pokemon_cells = button.parent().parent().find('.pokemon');
  pokemon_cells.map((i, cell) => {
    let exp = $(cell).data('export');
    $(cell).append(`<div class='expand'>${exp}</div>`); // Change to list
  });
  button.text('Compress');
  button.toggleClass('expanded');
}

function compressRow(button) {
  if (!$(button).hasClass('expanded')) return;
  let pokemon_cells = button.parent().parent().find('.pokemon');
  pokemon_cells.find('.expand').remove();
  button.text('Expand');
  button.toggleClass('expanded');
}

function addSave() {
  $('#save-form').submit( (e, f) => {
      e.preventDefault();
      $.ajax({
        type: 'POST',
        url: $('#save-form').data('url'),
        data: {
          serialization: serialize(),
          scout_id: $('#save-form').data('scout-id'),
          csrfmiddlewaretoken: $(e.target).serializeArray()[0].value
        },
        success: (res) => {
          let url = res.url;
          window.history.replaceState('', '', url);
          $('#save-form').data('scout-id', res.scout_id);
        }
      })
  })
}