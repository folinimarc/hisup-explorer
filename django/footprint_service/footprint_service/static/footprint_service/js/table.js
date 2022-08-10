"use strict";

class DatatablesWrapper {
  constructor(conf) {
    this.domElementId = conf["domElementId"] || "table";
    this.table = $(`#${this.domElementId}`).DataTable(conf['tableConf'] || {});
    this.highlightedRow = null;

    // Periodic reload
    setInterval( () => {
      this.table.ajax.reload(() => {
        this.refreshRowHighlight();
      });
    }, 10000 );
  }

  setRowHighlight(rowId) {
    this.highlightedRow = rowId;
    this.refreshRowHighlight();
  }

  refreshRowHighlight() {
    if (this.highlightedRow) {
      // Remove class highlight from all rows, then add to selected.
      this.table.rows().every(function() {
        this.nodes().to$().removeClass('highlight');
      })
      this.table.row(`#${this.highlightedRow}`).nodes().to$().addClass('highlight');
    }
  }
}
