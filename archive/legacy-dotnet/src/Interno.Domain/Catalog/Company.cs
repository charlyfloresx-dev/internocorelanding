using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Domain.Catalog
{
    public class  Company {
        [Key]
        public int Id { get; set; }

        [Required]
        [MaxLength (45)]
        public string Code { get; set; }
        [Required]
        [MaxLength (45)]
        public string Name { get; set; }
        [MaxLength (150)]
        public string BussinesName { get; set; }
        [Url]
        public string Web { get; set; }

        public virtual ICollection<Contact> Contacts { get; set; }
        public virtual ICollection<Location> Locations { get; set; }

        public virtual Phone BussinesPhone { get; set; }

        //[StringLength(50, ErrorMessage = "Enter Valid RFC."),RegularExpression(@"^([A-ZÑ\x26]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))((-)?([A-Z\d]{3}))?$")]
        //public string RFC{ get; set; }

        [Url]
        public string PrivacyPolicy { get; set; }
        //[Required]
        [MaxLength (100)]
        public string BussinessType { get; set; }
        //public FileData Logo { get; set; }
        [MaxLength (250)]
        public string Observations { get; set; }
        [NotMapped]
        public virtual ICollection<Miscellaneous> Miscellaneous { get; set;}

        [DatabaseGenerated (DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        [TimestampAttribute]
        [DatabaseGenerated (DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;
        [DataType (DataType.DateTime)]
        public DateTime DeleteDate { get; set; }
        public bool Delete { get; set; }
    }
}