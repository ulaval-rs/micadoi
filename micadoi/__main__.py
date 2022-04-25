import mica

import datacite
import click


@click.group()
class group:
    pass


group.add_command(mica.extract)
# group.add_command(datacite.get_doi)
group.add_command(datacite.generate_mica_doi)
# group.add_command(datacite.update_doi)
# group.add_command(datacite.publish_doi)

if __name__ == "__main__":
    group()
