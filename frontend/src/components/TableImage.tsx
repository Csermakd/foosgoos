import FooseballTable from "../assets/foosball_table.svg";

/**
 * The centrepiece both match screens are built around.
 *
 * Sized by height rather than width: the artwork is strongly portrait, so
 * `max-w-xl` alone let it grow to roughly a full screen tall and shove the
 * start button and roster panels out of the same view.
 */
const TableImage = () => (
  <img
    src={FooseballTable}
    alt="Foosball table"
    className="max-h-[58vh] w-auto max-w-full"
  />
);

export default TableImage;
