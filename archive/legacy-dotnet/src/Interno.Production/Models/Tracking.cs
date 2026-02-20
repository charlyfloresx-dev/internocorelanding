using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Tracking
    {
        [Required]
        public string Reference { get; set; } // PO/MO/CO/DO/WO
        [Required]
        public int ResourceId { get; set; }
        public virtual Resource Resource { get; set; }
        public int OperationTimeId { get; set; }
        public virtual OperationTime OperationTime { get; set; }
        public string Item { get; set ; } //WorkOrder->Item
        public string Alias { get; set; }
        // References
        public string Series { get; set; }//Lot
        public string Sheet { get; set; } // Folio
        public string TrackingNumber { get; set; }
        [Required]
        public decimal Qty { get; set; }
        [MaxLength(100)]
        public string Responsible { get; set; }//Linea, Familia, Persona
        [MaxLength(100)]
        public string Target { get; set; }//Linea, Familia

        [Column(TypeName = "decimal(16, 4)")]
        public decimal Cost { get; set; }
        [MaxLength(250)]
        public string Comment { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Start { get; set; }
        public Interno.HumanResource.Models.Employee StartEmployee { get; set; }
        public DateTime Close { get; set; }
        public Interno.HumanResource.Models.Employee CloseEmployee { get; set; }
        public DateTime Reject { get; set; }
        public Interno.HumanResource.Models.Employee RejectEmployee { get; set; }

        public TimeSpan Transcurred { 
            get{ return (this.Close != DateTime.MinValue)? this.Close - this.Start : TimeSpan.Zero ; } 
        }

        
    }
}