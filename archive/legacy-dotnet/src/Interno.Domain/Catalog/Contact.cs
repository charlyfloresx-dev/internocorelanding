using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Catalog
{
    public class Contact
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public virtual Person Person { get; set; }
        [MaxLength (100)]
        public string JobTitle { get; set; }
        [MaxLength (45)]
        //Autority
        public string Department { get; set; }
        [MaxLength (100)]
        public string BusinessName { get; set; }
        [MaxLength (100)]
        public string Manager { get; set; }
        [MaxLength (250)]
        public string Notes { get; set; }

        public virtual ICollection<Phone> Phones { get; set; }
        public virtual ICollection<Mail> Mails { get; set; }

        public int CompanyId { get; set; }
        public virtual Company Company { get; set; }
    }
}