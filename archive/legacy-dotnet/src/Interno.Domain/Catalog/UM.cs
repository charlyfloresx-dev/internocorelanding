using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Domain.Catalog
{
    public class UM
    {
        [Key]
        [MaxLength (4)]
        public string Code { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        
        [MaxLength(50)]
        public string Plural { get; set; }

        public Interno.Domain.Catalog.UM[] initialList()
        {
            var um = new Interno.Domain.Catalog.UM[]
                    {
                    new Interno.Domain.Catalog.UM {Code= "5GL", Name="5 GALLON"},
                    new Interno.Domain.Catalog.UM {Code= "BF", Name="BOARD FT"},
                    new Interno.Domain.Catalog.UM {Code= "BX", Name="BOX"},
                    new Interno.Domain.Catalog.UM {Code= "C2", Name="SQUARE CENTIMETER - JB CDZ"},
                    new Interno.Domain.Catalog.UM {Code= "CI", Name="CUBIC INCH"},
                    new Interno.Domain.Catalog.UM {Code= "CL", Name="CENTILITER"},
                    new Interno.Domain.Catalog.UM {Code= "CM", Name="CENTIMETER"},
                    new Interno.Domain.Catalog.UM {Code= "CS", Name="CASE"},
                    new Interno.Domain.Catalog.UM {Code= "D3", Name="DECIMETER CUBE"},
                    new Interno.Domain.Catalog.UM {Code= "DM", Name="DECIMETER"},
                    new Interno.Domain.Catalog.UM {Code= "DR", Name="DRUM"},
                    new Interno.Domain.Catalog.UM {Code= "F3", Name="CUBIC FEET"},
                    new Interno.Domain.Catalog.UM {Code= "FT", Name="FEET"},
                    new Interno.Domain.Catalog.UM {Code= "GL", Name="GALLON"},
                    new Interno.Domain.Catalog.UM {Code= "GR", Name="GRAM"},
                    new Interno.Domain.Catalog.UM {Code= "IN", Name="INCH"},
                    new Interno.Domain.Catalog.UM {Code= "KG", Name="KILOGRAM"},
                    new Interno.Domain.Catalog.UM {Code= "KT", Name="KIT"},
                    new Interno.Domain.Catalog.UM {Code= "L", Name="LITER"},
                    new Interno.Domain.Catalog.UM {Code= "LB", Name="POUND"},
                    new Interno.Domain.Catalog.UM {Code= "LF", Name="LINEAR FEET"},
                    new Interno.Domain.Catalog.UM {Code= "LY", Name="LINEAR YARD"},
                    new Interno.Domain.Catalog.UM {Code= "M", Name="METER"},
                    new Interno.Domain.Catalog.UM {Code= "M2", Name="SQUARE METER"},
                    new Interno.Domain.Catalog.UM {Code= "M3", Name="CUBIC METER"},
                    new Interno.Domain.Catalog.UM {Code= "MO", Name="MONTHS"},
                    new Interno.Domain.Catalog.UM {Code= "OZ", Name="OUNCE"},
                    new Interno.Domain.Catalog.UM {Code= "PK", Name="PACK"},
                    new Interno.Domain.Catalog.UM {Code= "PR", Name="PAIR"},
                    new Interno.Domain.Catalog.UM {Code= "PT", Name="PINT"},
                    new Interno.Domain.Catalog.UM {Code= "QT", Name="QUART"},
                    new Interno.Domain.Catalog.UM {Code= "RL", Name="ROLL"},
                    new Interno.Domain.Catalog.UM {Code= "SF", Name="SQUARE FOOT"},
                    new Interno.Domain.Catalog.UM {Code= "SH", Name="SHEET"},
                    new Interno.Domain.Catalog.UM {Code= "SI", Name="SQUARE INCH"},
                    new Interno.Domain.Catalog.UM {Code= "SP", Name="SPOOL"},
                    new Interno.Domain.Catalog.UM {Code= "SY", Name="SQUARE YARD"},
                    new Interno.Domain.Catalog.UM {Code= "TB", Name="TUBE"},
                    new Interno.Domain.Catalog.UM {Code= "UN", Name="UNIT"},
                    new Interno.Domain.Catalog.UM {Code= "YD", Name="YARD"}
                    };
            return um;
        }
    }
}