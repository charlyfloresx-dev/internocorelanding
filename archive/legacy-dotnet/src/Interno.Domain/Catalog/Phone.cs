using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

using Interno.Domain.Enum;

namespace Interno.Domain.Catalog
{
    public class Phone
    {
        [Key]
        public int Id { get; set; }
        [Required(ErrorMessage = "Your must provide a Phone Number")]
        [Display(Name = "Phone Number")]
        [DataType(DataType.PhoneNumber)]
        [RegularExpression(@"^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$", ErrorMessage = "Not a valid Phone Number")]
        [MaxLength (13)]
        public string PhoneNumber { get; set; }
         [MaxLength (13)]
        public string PhoneExtension { get; set; }
        public virtual AddressType Type { get; set; } 
    }
}